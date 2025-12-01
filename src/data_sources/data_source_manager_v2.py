"""
DataSourceManager v2 - Enterprise-grade ingestion orchestrator.
Full integration with all sources, unified payload, fault isolation, AI enhancement.
"""

import os
import yaml
import traceback
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions

from .base import SourceClientBase
from .registry import SourceRegistry
from .safe_executor import SafeExecutor
from .utils import normalize_drug_name, sanitize_text, estimate_confidence, estimate_severity

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("data_source_config.yaml")
ENV_PATH = Path(".env")


class DataSourceManagerV2:
    """
    Master orchestrator for all AE data sources (v2).
    
    Features:
    - Loads all clients dynamically
    - Handles config + env
    - Executes fetch safely with retry
    - Normalizes payloads to unified format
    - AI-enhanced confidence and severity scoring
    - Fault isolation (one bad source never breaks the pipeline)
    """
    
    def __init__(self, config_path: Optional[Path] = None, env_path: Optional[Path] = None):
        """
        Initialize DataSourceManager v2.
        
        Args:
            config_path: Path to datasources.yaml
            env_path: Path to .env file
        """
        self.config_path = config_path or CONFIG_PATH
        self.env_path = env_path or ENV_PATH
        self.config = self._load_config()
        self.env_cache = self._load_env()
        self.registry = SourceRegistry(config_path=self.config_path)
        self.clients: Dict[str, SourceClientBase] = {}
        self._initialize_clients()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {"sources": {}}
        
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {"sources": {}}
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {"sources": {}}
    
    def _load_env(self) -> Dict[str, str]:
        """Load .env file into dictionary."""
        env_dict = {}
        if self.env_path.exists():
            try:
                with open(self.env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            env_dict[key.strip()] = val.strip().strip('"').strip("'")
            except Exception as e:
                logger.error(f"Error loading .env: {str(e)}")
        return env_dict
    
    def has_key(self, src: str) -> bool:
        """
        Check if a source has its required API key.
        
        Args:
            src: Source name
            
        Returns:
            True if key is present (or not required)
        """
        cfg = self.config.get("sources", {}).get(src, {})
        key_env = cfg.get("api_key_env") or cfg.get("key_env")
        
        if not key_env:
            return True  # No key required
        
        # Check both environment and cache
        return bool(os.getenv(key_env, "") or self.env_cache.get(key_env, ""))
    
    def is_enabled(self, src: str) -> bool:
        """
        Determine if a source is enabled.
        
        Args:
            src: Source name
            
        Returns:
            True if source is enabled
        """
        cfg = self.config.get("sources", {}).get(src, {})
        mode = cfg.get("enabled", False)
        
        # Hard enabled
        if mode is True or mode == "true":
            return True
        
        # Hard disabled
        if mode is False or mode == "false":
            return False
        
        # Auto mode: enabled only if key exists
        if mode == "auto":
            return self.has_key(src)
        
        return False
    
    def _initialize_clients(self):
        """Dynamically load all clients from registry."""
        try:
            # Get all sources from registry
            all_sources = self.registry.get_all_sources()
            
            for src in all_sources:
                # Check if enabled
                if self.is_enabled(src.name):
                    self.clients[src.name] = src
                else:
                    logger.info(f"Source {src.name} is disabled (mode: {self.config.get('sources', {}).get(src.name, {}).get('enabled')})")
            
            logger.info(f"Initialized {len(self.clients)} enabled data sources")
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            logger.error(traceback.format_exc())
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _safe_fetch(self, client: SourceClientBase, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Safe fetch with retry logic.
        
        Args:
            client: Source client instance
            query: Query parameters
            
        Returns:
            List of raw entries from source
        """
        return client.fetch(query)
    
    def fetch_all(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute fetch for all enabled sources and merge results.
        
        Args:
            query: Query parameters (drug_name, reaction, date_range, etc.)
            
        Returns:
            List of unified AE entries from all sources
        """
        results = []
        
        # Sort by priority (higher first)
        sorted_clients = sorted(
            self.clients.items(),
            key=lambda x: getattr(x[1], 'priority', 0),
            reverse=True
        )
        
        for src_name, client in sorted_clients:
            if not self.is_enabled(src_name):
                continue
            
            try:
                # Fetch with retry
                raw_entries = self._safe_fetch(client, query)
                
                if not raw_entries:
                    continue
                
                # Normalize each entry
                for entry in raw_entries:
                    unified = self._unify_entry(entry, src_name)
                    if unified:
                        results.append(unified)
            
            except Exception as e:
                # Fault isolation: log error but continue with other sources
                logger.warning(f"Source {src_name} failed: {str(e)}")
                logger.debug(traceback.format_exc())
                continue
        
        logger.info(f"Fetched {len(results)} unified entries from {len(self.clients)} sources")
        return results
    
    def fetch_by_source(self, source_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch from a specific source.
        
        Args:
            source_name: Name of the source
            query: Query parameters
            
        Returns:
            List of unified AE entries
        """
        if source_name not in self.clients:
            logger.warning(f"Source not found or disabled: {source_name}")
            return []
        
        client = self.clients[source_name]
        
        try:
            raw_entries = self._safe_fetch(client, query)
            results = []
            
            for entry in raw_entries:
                unified = self._unify_entry(entry, source_name)
                if unified:
                    results.append(unified)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {str(e)}")
            return []
    
    def _unify_entry(self, entry: Dict[str, Any], src: str) -> Optional[Dict[str, Any]]:
        """
        Unify payload structure to standard AE format.
        
        Args:
            entry: Raw entry from source
            src: Source name
            
        Returns:
            Unified entry or None if invalid
        """
        try:
            # Extract basic fields
            text = entry.get("text") or entry.get("description") or entry.get("narrative") or ""
            drug = entry.get("drug") or entry.get("drug_name") or entry.get("drug_match") or ""
            reaction = entry.get("reaction") or entry.get("adverse_event") or entry.get("event") or ""
            timestamp = entry.get("timestamp") or entry.get("date") or entry.get("created_date")
            
            # Sanitize and normalize
            text = sanitize_text(text)
            drug = normalize_drug_name(drug) if drug else ""
            
            # Skip if missing essential fields
            if not text and not reaction:
                return None
            
            # AI-enhanced scoring
            confidence = entry.get("confidence")
            if confidence is None:
                confidence = estimate_confidence(text)
            
            severity = entry.get("severity")
            if severity is None:
                severity = estimate_severity(text)
            
            # Build unified entry
            unified = {
                "timestamp": timestamp,
                "drug": drug,
                "reaction": reaction,
                "confidence": float(confidence),
                "severity": float(severity),
                "text": text,
                "source": src,
                "metadata": entry.get("metadata", {})
            }
            
            # Preserve original fields in metadata if not already there
            if "original_entry" not in unified["metadata"]:
                unified["metadata"]["original_entry"] = entry
            
            return unified
        
        except Exception as e:
            logger.error(f"Failed to unify entry from {src}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_source_status(self, source_name: str) -> Dict[str, Any]:
        """
        Get status information for a source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Status dictionary
        """
        cfg = self.config.get("sources", {}).get(source_name, {})
        
        return {
            "name": source_name,
            "enabled": self.is_enabled(source_name),
            "has_key": self.has_key(source_name),
            "api_key_env": cfg.get("api_key_env") or cfg.get("key_env"),
            "priority": cfg.get("priority", 0),
            "fallback_mode": cfg.get("fallback", "silent"),
            "metadata": cfg.get("metadata", {})
        }
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all sources.
        
        Returns:
            Dictionary mapping source names to status
        """
        all_sources = set(self.config.get("sources", {}).keys())
        all_sources.update(self.clients.keys())
        
        return {
            source_name: self.get_source_status(source_name)
            for source_name in all_sources
        }

