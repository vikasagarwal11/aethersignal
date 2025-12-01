"""
Data Source Manager - Core brain of the ingestion system.
Handles source detection, fallback routing, and unified output format.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .safe_executor import SafeExecutor, safe_fetch
from .registry import SourceRegistry

logger = logging.getLogger(__name__)


class FallbackMode(Enum):
    """Fallback behavior modes."""
    SILENT = "silent"  # Skip silently, no warnings
    WARNING = "warning"  # Show soft warning
    DUMMY = "dummy"  # Return dummy data for testing


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    name: str
    enabled: bool = True
    fallback_mode: FallbackMode = FallbackMode.SILENT
    api_key_env: Optional[str] = None  # Environment variable name for API key
    api_key_present: bool = False
    priority: int = 0  # Higher priority = tried first
    last_fetch: Optional[datetime] = None
    fetch_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataSourceManager:
    """
    Manages all data sources with automatic detection, fallback, and routing.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        env_file: Optional[Path] = None
    ):
        """
        Initialize data source manager.
        
        Args:
            config_path: Path to data_source_config.yaml
            env_file: Path to .env file
        """
        self.config_path = config_path or Path("data_source_config.yaml")
        self.env_file = env_file or Path(".env")
        self.sources: Dict[str, DataSourceConfig] = {}
        self.executor = SafeExecutor("DataSourceManager")
        self.registry = SourceRegistry(config_path=self.config_path)
        self._load_config()
        self._detect_api_keys()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.info(f"Config file not found: {self.config_path}. Using defaults.")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            
            sources_config = config_data.get('sources', {})
            
            for source_name, source_data in sources_config.items():
                fallback_str = source_data.get('fallback', 'silent')
                fallback_mode = FallbackMode(fallback_str)
                
                self.sources[source_name] = DataSourceConfig(
                    name=source_name,
                    enabled=source_data.get('enabled', True),
                    fallback_mode=fallback_mode,
                    api_key_env=source_data.get('api_key_env'),
                    priority=source_data.get('priority', 0),
                    metadata=source_data.get('metadata', {})
                )
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}. Using defaults.")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration."""
        default_sources = {
            'reddit': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 10
            },
            'openfda': {
                'enabled': True,
                'fallback': 'silent',
                'api_key_env': 'OPENFDA_API_KEY',
                'priority': 9
            },
            'pubmed': {
                'enabled': True,
                'fallback': 'silent',
                'api_key_env': 'PUBMED_API_KEY',
                'priority': 8
            },
            'clinicaltrials': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 7
            },
            'dailymed': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 6
            },
            'ema_prac': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 5
            },
            'mhra': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 5
            },
            'health_canada': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 5
            },
            'tga_australia': {
                'enabled': True,
                'fallback': 'silent',
                'priority': 5
            },
            'drugs_com': {
                'enabled': True,
                'fallback': 'warning',
                'priority': 4
            },
            'patient_info': {
                'enabled': True,
                'fallback': 'warning',
                'priority': 4
            },
            'google_places': {
                'enabled': True,
                'fallback': 'silent',
                'api_key_env': 'GOOGLE_PLACES_API_KEY',
                'priority': 3
            },
            # Paid sources
            'human_api': {
                'enabled': False,
                'fallback': 'warning',
                'api_key_env': 'HUMAN_API_KEY',
                'priority': 2
            },
            'metriport': {
                'enabled': False,
                'fallback': 'warning',
                'api_key_env': 'METRIPORT_API_KEY',
                'priority': 2
            },
            'drugbank': {
                'enabled': False,
                'fallback': 'silent',
                'api_key_env': 'DRUGBANK_KEY',
                'priority': 1
            },
            'vigibase': {
                'enabled': False,
                'fallback': 'warning',
                'api_key_env': 'VIGIBASE_KEY',
                'priority': 1
            },
            'epic_fhir': {
                'enabled': False,
                'fallback': 'dummy',
                'api_key_env': 'EPIC_FHIR_KEY',
                'priority': 1
            },
            'cerner_fhir': {
                'enabled': False,
                'fallback': 'dummy',
                'api_key_env': 'CERNER_FHIR_KEY',
                'priority': 1
            },
            'ohdsi': {
                'enabled': False,
                'fallback': 'warning',
                'api_key_env': 'OHDSI_KEY',
                'priority': 1
            }
        }
        
        for source_name, source_data in default_sources.items():
            fallback_mode = FallbackMode(source_data['fallback'])
            self.sources[source_name] = DataSourceConfig(
                name=source_name,
                enabled=source_data.get('enabled', True),
                fallback_mode=fallback_mode,
                api_key_env=source_data.get('api_key_env'),
                priority=source_data.get('priority', 0),
                metadata=source_data.get('metadata', {})
            )
    
    def _detect_api_keys(self):
        """Detect which API keys are present in environment."""
        for source in self.sources.values():
            if source.api_key_env:
                source.api_key_present = bool(os.getenv(source.api_key_env))
    
    def is_enabled(self, source_name: str) -> bool:
        """Check if a source is enabled."""
        if source_name not in self.sources:
            return False
        return self.sources[source_name].enabled
    
    def get_fallback_mode(self, source_name: str) -> FallbackMode:
        """Get fallback mode for a source."""
        if source_name not in self.sources:
            return FallbackMode.SILENT
        return self.sources[source_name].fallback_mode
    
    def get_enabled_sources(self, include_disabled: bool = False) -> List[str]:
        """
        Get list of enabled sources, optionally including disabled ones.
        
        Args:
            include_disabled: If True, include disabled sources (for admin view)
        
        Returns:
            List of source names, sorted by priority
        """
        sources = []
        for source_name, config in self.sources.items():
            if config.enabled or include_disabled:
                sources.append((source_name, config.priority))
        
        # Sort by priority (higher first)
        sources.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in sources]
    
    def fetch_all(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch from all enabled sources and merge results.
        
        Args:
            query: Query parameters (drug_name, reaction, date_range, etc.)
        
        Returns:
            List of unified AE entries from all sources
        """
        results = []
        
        for src in self.registry.get_enabled_sources():
            try:
                data = src.safe_fetch(query)
                if data:
                    # Ensure all entries have source name
                    for item in data:
                        if "source" not in item:
                            item["source"] = src.name
                    results.extend(data)
            except Exception as e:
                logger.error(f"Error fetching from {src.name}: {str(e)}")
                # Continue with other sources
        
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
        src = self.registry.get(source_name)
        if not src:
            logger.warning(f"Source not found: {source_name}")
            return []
        
        return src.safe_fetch(query)
    
    def fetch_with_fallback(
        self,
        source_name: str,
        fetch_func: Callable,
        *args,
        fallback_func: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Fetch data from a source with automatic fallback handling.
        (Legacy method for backward compatibility)
        
        Args:
            source_name: Name of the data source
            fetch_func: Function to fetch data
            *args: Arguments for fetch_func
            fallback_func: Optional fallback function
            **kwargs: Keyword arguments for fetch_func
        
        Returns:
            Fetched data or fallback result
        """
        if source_name not in self.sources:
            logger.warning(f"Unknown source: {source_name}")
            return None
        
        config = self.sources[source_name]
        
        # Check if source is enabled
        if not config.enabled:
            return self._handle_disabled_source(config)
        
        # Check if API key is required and present
        if config.api_key_env and not config.api_key_present:
            return self._handle_missing_key(config)
        
        # Attempt fetch with retry logic
        try:
            result = safe_fetch(
                fetch_func,
                *args,
                fallback_func=fallback_func,
                executor=self.executor,
                **kwargs
            )
            
            # Update stats
            config.last_fetch = datetime.now()
            config.fetch_count += 1
            
            return result
        except Exception as e:
            config.error_count += 1
            config.last_error = str(e)
            logger.error(f"Error fetching from {source_name}: {str(e)}")
            return self._handle_fetch_error(config, fallback_func, *args, **kwargs)
    
    def _handle_disabled_source(self, config: DataSourceConfig) -> Any:
        """Handle disabled source based on fallback mode."""
        if config.fallback_mode == FallbackMode.SILENT:
            return None
        elif config.fallback_mode == FallbackMode.WARNING:
            logger.info(f"Source {config.name} is disabled. Add API key to enable.")
            return None
        elif config.fallback_mode == FallbackMode.DUMMY:
            return self._get_dummy_data(config.name)
        return None
    
    def _handle_missing_key(self, config: DataSourceConfig) -> Any:
        """Handle missing API key based on fallback mode."""
        if config.fallback_mode == FallbackMode.SILENT:
            return None
        elif config.fallback_mode == FallbackMode.WARNING:
            logger.info(
                f"Source {config.name} requires API key ({config.api_key_env}). "
                "Add key to enable."
            )
            return None
        elif config.fallback_mode == FallbackMode.DUMMY:
            return self._get_dummy_data(config.name)
        return None
    
    def _handle_fetch_error(
        self,
        config: DataSourceConfig,
        fallback_func: Optional[Callable],
        *args,
        **kwargs
    ) -> Any:
        """Handle fetch error based on fallback mode."""
        if config.fallback_mode == FallbackMode.SILENT:
            return None
        elif config.fallback_mode == FallbackMode.WARNING:
            logger.warning(f"Failed to fetch from {config.name}: {config.last_error}")
            return None
        elif config.fallback_mode == FallbackMode.DUMMY:
            if fallback_func:
                try:
                    return fallback_func(*args, **kwargs)
                except Exception:
                    pass
            return self._get_dummy_data(config.name)
        return None
    
    def _get_dummy_data(self, source_name: str) -> List[Dict]:
        """Get dummy data for testing/demo purposes."""
        return [
            {
                "source": source_name,
                "text": f"Sample adverse event from {source_name}",
                "drug": "sample_drug",
                "reaction": "sample_reaction",
                "date": datetime.now().isoformat(),
                "is_dummy": True
            }
        ]
    
    def get_source_status(self, source_name: str) -> Dict[str, Any]:
        """Get status information for a source."""
        if source_name not in self.sources:
            return {}
        
        config = self.sources[source_name]
        return {
            "name": config.name,
            "enabled": config.enabled,
            "fallback_mode": config.fallback_mode.value,
            "api_key_present": config.api_key_present,
            "api_key_env": config.api_key_env,
            "priority": config.priority,
            "last_fetch": config.last_fetch.isoformat() if config.last_fetch else None,
            "fetch_count": config.fetch_count,
            "error_count": config.error_count,
            "last_error": config.last_error,
            "metadata": config.metadata
        }
    
    def get_all_sources_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all sources (for admin dashboard)."""
        return {
            source_name: self.get_source_status(source_name)
            for source_name in self.sources.keys()
        }
    
    def superadmin_metadata(self) -> List[Dict[str, Any]]:
        """
        Provides diagnostic info for admin UI.
        Returns metadata for all sources (enabled and disabled).
        """
        meta = []
        
        # Get from registry (if sources are registered)
        for src in self.registry.get_all_sources():
            meta.append({
                "name": src.name,
                "enabled": src.enabled,
                "fallback": src.fallback_mode,
                "class": src.__class__.__name__,
                "has_api_key": self._check_key(src.name),
                "priority": src.priority,
                "metadata": src.metadata
            })
        
        # Also include config-based sources (for backward compatibility)
        for source_name, config in self.sources.items():
            if not any(m["name"] == source_name for m in meta):
                meta.append({
                    "name": source_name,
                    "enabled": config.enabled,
                    "fallback": config.fallback_mode.value,
                    "class": "ConfigBasedSource",
                    "has_api_key": config.api_key_present,
                    "priority": config.priority,
                    "metadata": config.metadata
                })
        
        return sorted(meta, key=lambda x: x.get("priority", 0), reverse=True)
    
    def save_config(self):
        """Save current configuration to YAML file."""
        config_data = {
            'sources': {
                source_name: {
                    'enabled': config.enabled,
                    'fallback': config.fallback_mode.value,
                    'api_key_env': config.api_key_env,
                    'priority': config.priority,
                    'metadata': config.metadata
                }
                for source_name, config in self.sources.items()
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {self.config_path}")

