"""
Offline Cache Bridge (CHUNK 7.9)
Python bridge to browser-side offline cache (IndexedDB via JavaScript).
"""
import streamlit as st
from typing import Any, Optional, Dict
import json


def save_to_cache(key: str, value: Any) -> bool:
    """
    Save data to browser-side offline cache.
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON-serializable)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Store in session state for now (can be enhanced with JS bridge)
        if "offline_cache" not in st.session_state:
            st.session_state["offline_cache"] = {}
        
        st.session_state["offline_cache"][key] = value
        
        # Also try to persist via JavaScript if available
        try:
            import streamlit.components.v1 as components
            
            cache_js = f"""
            <script>
                if (window.aetherOfflineCache) {{
                    window.aetherOfflineCache.save('{key}', {json.dumps(value)});
                }}
            </script>
            """
            components.html(cache_js, height=0)
        except Exception:
            pass  # Fallback to session state only
        
        return True
    except Exception as e:
        st.error(f"Error saving to cache: {e}")
        return False


def load_from_cache(key: str) -> Optional[Any]:
    """
    Load data from browser-side offline cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    try:
        # Check session state first
        if "offline_cache" in st.session_state:
            return st.session_state["offline_cache"].get(key)
        
        return None
    except Exception:
        return None


def clear_cache(key: str) -> bool:
    """
    Clear a specific cache entry.
    
    Args:
        key: Cache key to clear
        
    Returns:
        True if successful
    """
    try:
        if "offline_cache" in st.session_state:
            if key in st.session_state["offline_cache"]:
                del st.session_state["offline_cache"][key]
        
        # Also clear via JavaScript if available
        try:
            import streamlit.components.v1 as components
            
            clear_js = f"""
            <script>
                if (window.aetherOfflineCache) {{
                    window.aetherOfflineCache.clear('{key}');
                }}
            </script>
            """
            components.html(clear_js, height=0)
        except Exception:
            pass
        
        return True
    except Exception:
        return False


def clear_all_cache() -> bool:
    """
    Clear all cached data.
    
    Returns:
        True if successful
    """
    try:
        if "offline_cache" in st.session_state:
            st.session_state["offline_cache"] = {}
        
        # Also clear via JavaScript if available
        try:
            import streamlit.components.v1 as components
            
            clear_js = """
            <script>
                if (window.aetherOfflineCache) {
                    window.aetherOfflineCache.clearAll();
                }
            </script>
            """
            components.html(clear_js, height=0)
        except Exception:
            pass
        
        return True
    except Exception:
        return False


def get_cache_size() -> int:
    """
    Get approximate cache size.
    
    Returns:
        Number of cached items
    """
    try:
        if "offline_cache" in st.session_state:
            return len(st.session_state["offline_cache"])
        return 0
    except Exception:
        return 0

