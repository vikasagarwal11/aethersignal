"""
Hybrid Caching Layer (CHUNK 1 - Part 1.5)
Cost-saving cache for hybrid query results.

Caches expensive computation results to avoid redundant processing.
"""
import hashlib
import json
import streamlit as st
from typing import Dict, Any, Optional, Any


def hash_query(query: str, df_profile: Dict[str, Any]) -> str:
    """
    Generate cache key from query and dataset profile.
    
    Args:
        query: User query string
        df_profile: Dataset profile dictionary
        
    Returns:
        SHA256 hash string as cache key
    """
    key_data = {
        "query": query,
        "rows": df_profile.get("row_count", 0),
        "cols": df_profile.get("column_count", 0),
        "columns": sorted(df_profile.get("columns", []))[:10]  # First 10 columns for key
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


def get_from_cache(query: str, df_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get cached result for query.
    
    Args:
        query: User query string
        df_profile: Dataset profile dictionary
        
    Returns:
        Cached result dictionary or None
    """
    if not query or not df_profile:
        return None
    
    key = hash_query(query, df_profile)
    cache = st.session_state.setdefault("hybrid_cache", {})
    
    result = cache.get(key)
    
    # Add cache hit indicator
    if result:
        result["_cached"] = True
        result["_cache_key"] = key
    
    return result


def save_to_cache(query: str, df_profile: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Save query result to cache.
    
    Args:
        query: User query string
        df_profile: Dataset profile dictionary
        result: Result dictionary to cache
    """
    if not query or not df_profile or not result:
        return
    
    key = hash_query(query, df_profile)
    cache = st.session_state.setdefault("hybrid_cache", {})
    
    # Create cache entry with metadata
    cache_entry = {
        "result": result,
        "timestamp": st.session_state.get("_cache_timestamp", 0),
        "query": query[:100]  # Store first 100 chars for debugging
    }
    
    cache[key] = cache_entry
    
    # Limit cache size (keep last 50 entries)
    if len(cache) > 50:
        # Remove oldest entries (simple FIFO)
        keys = list(cache.keys())
        for old_key in keys[:-50]:
            del cache[old_key]


def clear_cache() -> None:
    """Clear all cached results."""
    if "hybrid_cache" in st.session_state:
        st.session_state["hybrid_cache"] = {}


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    cache = st.session_state.get("hybrid_cache", {})
    
    return {
        "size": len(cache),
        "keys": list(cache.keys())[:10]  # First 10 keys
    }

