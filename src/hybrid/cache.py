"""
Hybrid Summary Cache (CHUNK 7.4 Part 2)
Cache layer for hybrid summary generation to avoid recomputation.
"""
import time
from typing import Dict, Any, Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class HybridSummaryCache:
    """
    Cache for hybrid summary results.
    
    Provides:
    - Fast lookups (milliseconds instead of seconds)
    - Automatic expiration
    - Session-scoped storage
    """
    
    def __init__(self, expiry_seconds: int = 300):
        """
        Initialize Hybrid Summary Cache.
        
        Args:
            expiry_seconds: Cache expiry time in seconds (default: 5 minutes)
        """
        self.expiry_seconds = expiry_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
        
        # Initialize session state cache if Streamlit available
        if STREAMLIT_AVAILABLE:
            if "hybrid_summary_cache" not in st.session_state:
                st.session_state.hybrid_summary_cache = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached summary.
        
        Args:
            key: Cache key
            
        Returns:
            Cached summary or None if not found or expired
        """
        # Check in-memory cache
        entry = self.cache.get(key)
        if entry:
            data, timestamp = entry
            if time.time() - timestamp < self.expiry_seconds:
                return data
            else:
                # Expired - remove from cache
                del self.cache[key]
        
        # Check session state cache
        if STREAMLIT_AVAILABLE:
            session_cache = st.session_state.get("hybrid_summary_cache", {})
            if key in session_cache:
                entry = session_cache[key]
                if isinstance(entry, dict):
                    timestamp = entry.get("_cache_timestamp", 0)
                    if time.time() - timestamp < self.expiry_seconds:
                        # Return copy without timestamp metadata
                        result = entry.copy()
                        result.pop("_cache_timestamp", None)
                        return result
                    else:
                        # Expired - remove
                        del session_cache[key]
        
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """
        Store summary in cache.
        
        Args:
            key: Cache key
            value: Summary dictionary to cache
        """
        timestamp = time.time()
        
        # Store in-memory cache
        self.cache[key] = (value, timestamp)
        
        # Store in session state cache
        if STREAMLIT_AVAILABLE:
            if "hybrid_summary_cache" not in st.session_state:
                st.session_state.hybrid_summary_cache = {}
            
            # Add timestamp metadata
            cached_value = value.copy()
            cached_value["_cache_timestamp"] = timestamp
            st.session_state.hybrid_summary_cache[key] = cached_value
        
        # Limit cache size (keep last 50 entries)
        if len(self.cache) > 50:
            # Remove oldest entries
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            for old_key, _ in sorted_items[:10]:
                del self.cache[old_key]
    
    def clear(self):
        """Clear all cached summaries."""
        self.cache.clear()
        
        if STREAMLIT_AVAILABLE:
            if "hybrid_summary_cache" in st.session_state:
                st.session_state.hybrid_summary_cache.clear()

