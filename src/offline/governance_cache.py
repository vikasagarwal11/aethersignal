"""
Offline Governance Cache (CHUNK B3)
Stores governance artifacts locally for offline access.
"""
import json
import time
from typing import Dict, Any, Optional, List

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class GovernanceCache:
    """
    Local cache for governance artifacts.
    
    Stores:
    - Trend alerts
    - RPF scores
    - CAPA recommendations
    - Benefit-Risk assessments
    - Inspector Q&A responses
    - Governance PDFs
    - Signal files
    """
    
    def __init__(self):
        """Initialize Governance Cache."""
        self.cache: Dict[str, tuple[Any, float]] = {}
        
        # Initialize session state cache if Streamlit available
        if STREAMLIT_AVAILABLE:
            if "offline_governance_cache" not in st.session_state:
                st.session_state.offline_governance_cache = {}
    
    def put(self, key: str, value: Any, expiry_seconds: Optional[int] = None):
        """
        Store governance artifact in cache.
        
        Args:
            key: Cache key
            value: Data to cache
            expiry_seconds: Optional expiry time (default: no expiry)
        """
        timestamp = time.time()
        expiry = timestamp + expiry_seconds if expiry_seconds else None
        
        # Store in-memory cache
        self.cache[key] = (value, timestamp, expiry)
        
        # Store in session state cache
        if STREAMLIT_AVAILABLE:
            if "offline_governance_cache" not in st.session_state:
                st.session_state.offline_governance_cache = {}
            
            cached_value = {
                "data": value,
                "timestamp": timestamp,
                "expiry": expiry
            }
            st.session_state.offline_governance_cache[key] = cached_value
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve governance artifact from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found or expired
        """
        # Check in-memory cache
        entry = self.cache.get(key)
        if entry:
            value, timestamp, expiry = entry
            if expiry is None or time.time() < expiry:
                return value
            else:
                # Expired - remove from cache
                del self.cache[key]
        
        # Check session state cache
        if STREAMLIT_AVAILABLE:
            session_cache = st.session_state.get("offline_governance_cache", {})
            if key in session_cache:
                entry = session_cache[key]
                if isinstance(entry, dict):
                    expiry = entry.get("expiry")
                    if expiry is None or time.time() < expiry:
                        return entry.get("data")
                    else:
                        # Expired - remove
                        del session_cache[key]
        
        return None
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache and is not expired."""
        return self.get(key) is not None
    
    def delete(self, key: str):
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
        
        if STREAMLIT_AVAILABLE:
            session_cache = st.session_state.get("offline_governance_cache", {})
            if key in session_cache:
                del session_cache[key]
    
    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        
        if STREAMLIT_AVAILABLE:
            if "offline_governance_cache" in st.session_state:
                st.session_state.offline_governance_cache.clear()
    
    def export(self) -> str:
        """
        Export cache to JSON string.
        
        Returns:
            JSON string representation of cache
        """
        export_data = {}
        current_time = time.time()
        
        for key, (value, timestamp, expiry) in self.cache.items():
            if expiry is None or current_time < expiry:
                export_data[key] = {
                    "data": value,
                    "timestamp": timestamp,
                    "expiry": expiry
                }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def import_cache(self, json_str: str):
        """
        Import cache from JSON string.
        
        Args:
            json_str: JSON string representation of cache
        """
        try:
            imported = json.loads(json_str)
            current_time = time.time()
            
            for key, entry in imported.items():
                if isinstance(entry, dict):
                    expiry = entry.get("expiry")
                    if expiry is None or current_time < expiry:
                        self.put(key, entry.get("data"))
        except json.JSONDecodeError:
            pass
    
    def list_keys(self) -> List[str]:
        """
        List all non-expired cache keys.
        
        Returns:
            List of cache keys
        """
        current_time = time.time()
        keys = []
        
        # In-memory cache
        for key, (_, _, expiry) in self.cache.items():
            if expiry is None or current_time < expiry:
                keys.append(key)
        
        # Session state cache
        if STREAMLIT_AVAILABLE:
            session_cache = st.session_state.get("offline_governance_cache", {})
            for key, entry in session_cache.items():
                if isinstance(entry, dict):
                    expiry = entry.get("expiry")
                    if expiry is None or current_time < expiry:
                        if key not in keys:
                            keys.append(key)
        
        return keys
    
    def size(self) -> int:
        """Get number of cached items."""
        return len(self.list_keys())


# Global singleton instance
_global_cache: Optional[GovernanceCache] = None


def get_governance_cache() -> GovernanceCache:
    """Get or create global Governance Cache instance."""
    global _global_cache
    
    if _global_cache is None:
        _global_cache = GovernanceCache()
    
    return _global_cache

