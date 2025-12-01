"""
Offline Cache Manager (CHUNK 7.9)
Manages IndexedDB cache for offline data persistence.
"""
from typing import Dict, List, Any, Optional
import json
import streamlit as st


class OfflineCacheManager:
    """
    Manages offline cache using IndexedDB (via JavaScript bridge).
    
    Stores:
    - Parsed FAERS data
    - Trend deltas
    - Cluster embeddings
    - Subgroup stats
    - Exported reports
    """
    
    def __init__(self):
        """Initialize cache manager."""
        self.cache_prefix = "aether_offline_"
    
    def save_to_cache(self, key: str, data: Any) -> bool:
        """
        Save data to offline cache.
        
        Args:
            key: Cache key
            data: Data to cache (must be JSON-serializable)
            
        Returns:
            True if successful
        """
        try:
            # Save to session state first (immediate availability)
            if "offline_cache" not in st.session_state:
                st.session_state.offline_cache = {}
            
            st.session_state.offline_cache[key] = data
            
            # Also save to persistent cache (IndexedDB via bridge)
            try:
                from src.ui.offline_cache_bridge import save_to_cache
                save_to_cache(self.cache_prefix + key, data)
            except Exception:
                pass  # Fallback to session state only
            
            return True
        except Exception as e:
            st.error(f"Error saving to cache: {e}")
            return False
    
    def load_from_cache(self, key: str) -> Optional[Any]:
        """
        Load data from offline cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        try:
            # Check session state first
            if "offline_cache" in st.session_state:
                if key in st.session_state.offline_cache:
                    return st.session_state.offline_cache[key]
            
            # Try persistent cache
            try:
                from src.ui.offline_cache_bridge import load_from_cache
                return load_from_cache(self.cache_prefix + key)
            except Exception:
                return None
        except Exception:
            return None
    
    def clear_cache(self, key: Optional[str] = None) -> bool:
        """
        Clear cache entry or all cache.
        
        Args:
            key: Optional specific key to clear. If None, clears all.
            
        Returns:
            True if successful
        """
        try:
            if key:
                # Clear specific key
                if "offline_cache" in st.session_state:
                    if key in st.session_state.offline_cache:
                        del st.session_state.offline_cache[key]
                
                try:
                    from src.ui.offline_cache_bridge import clear_cache
                    clear_cache(self.cache_prefix + key)
                except Exception:
                    pass
            else:
                # Clear all cache
                if "offline_cache" in st.session_state:
                    st.session_state.offline_cache = {}
                
                try:
                    from src.ui.offline_cache_bridge import clear_all_cache
                    clear_all_cache()
                except Exception:
                    pass
            
            return True
        except Exception:
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        cache = st.session_state.get("offline_cache", {})
        
        return {
            "entries": len(cache),
            "keys": list(cache.keys()),
            "total_size_estimate": sum(
                len(str(v).encode('utf-8')) for v in cache.values()
            ) if cache else 0
        }


def get_cache_manager() -> OfflineCacheManager:
    """
    Get or create cache manager instance.
    
    Returns:
        OfflineCacheManager instance
    """
    if "offline_cache_manager" not in st.session_state:
        st.session_state.offline_cache_manager = OfflineCacheManager()
    
    return st.session_state.offline_cache_manager

