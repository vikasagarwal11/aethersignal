"""
Base class for all data source clients.
Ensures consistent behavior across all sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .safe_executor import SafeExecutor, RetryConfig


class SourceClientBase(ABC):
    """
    Abstract base class for all data source implementations.
    All sources inherit from this to ensure consistent behavior.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize source client.
        
        Args:
            name: Source name (e.g., "openfda", "pubmed")
            config: Configuration dictionary from YAML
        """
        self.name = name
        self.enabled = config.get("enabled", False)
        self.fallback_mode = config.get("fallback", "silent")
        self.priority = config.get("priority", 0)
        self.metadata = config.get("metadata", {})
        
        # Create safe executor for this source
        retry_config = RetryConfig(
            attempts=3,
            min_wait=1,
            max_wait=10,
            multiplier=2,
            timeout_secs=20
        )
        self.executor = SafeExecutor(name, retry_config)
    
    @abstractmethod
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Actual fetch logic implemented by source subclasses.
        
        Args:
            query: Query parameters (drug_name, reaction, date_range, etc.)
        
        Returns:
            List of standardized AE entries
        """
        pass
    
    def fallback(self) -> List[Dict[str, Any]]:
        """
        Fallback behavior depending on mode.
        
        Returns:
            List of entries (empty, warning, or dummy data)
        """
        if self.fallback_mode == "silent":
            return []
        
        if self.fallback_mode == "warning":
            return [{
                "source": self.name,
                "warning": True,
                "message": f"{self.name} unavailable — enable source or add API key.",
                "timestamp": None,
                "drug": None,
                "reaction": None,
                "confidence": 0.0,
                "severity": 0.0,
                "text": None,
                "metadata": {}
            }]
        
        if self.fallback_mode == "dummy":
            return [{
                "source": self.name,
                "dummy": True,
                "timestamp": "2025-11-30",
                "drug": "exampledrug",
                "reaction": "nausea",
                "confidence": 0.5,
                "severity": 0.3,
                "text": f"Sample adverse event from {self.name} (dummy data)",
                "metadata": {
                    "is_dummy": True,
                    "source_name": self.name
                }
            }]
        
        return []
    
    def safe_fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Guaranteed safe to call — never breaks the pipeline.
        
        Args:
            query: Query parameters
        
        Returns:
            List of standardized AE entries (or fallback data)
        """
        if not self.enabled:
            return self.fallback()
        
        return self.executor.safe_execute(
            lambda: self.fetch(query),
            fallback=self.fallback
        )
    
    def normalize_entry(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw entry to unified format.
        Override in subclasses if needed.
        
        Args:
            raw_entry: Raw entry from source
        
        Returns:
            Normalized entry in unified format
        """
        return {
            "timestamp": raw_entry.get("timestamp") or raw_entry.get("date") or raw_entry.get("created_date"),
            "drug": raw_entry.get("drug") or raw_entry.get("drug_name") or raw_entry.get("drug_match"),
            "reaction": raw_entry.get("reaction") or raw_entry.get("adverse_event") or raw_entry.get("event"),
            "confidence": raw_entry.get("confidence", 0.0),
            "severity": raw_entry.get("severity", 0.0),
            "text": raw_entry.get("text") or raw_entry.get("description") or raw_entry.get("narrative"),
            "source": self.name,
            "metadata": raw_entry.get("metadata", {})
        }

