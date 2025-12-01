"""
AI Interpretation Caching (CHUNK B3)
Cache LLM interpretations to avoid repeat calls and reduce costs.
"""
import hashlib
import json
from functools import lru_cache
from typing import Optional, Dict, Any

# In-memory cache (can be extended to Redis/file storage)
_interpretation_cache: Dict[str, str] = {}


def hash_summary(summary: Dict[str, Any]) -> str:
    """
    Generate SHA256 hash of summary for cache key.
    
    Args:
        summary: Summary dictionary
        
    Returns:
        Hexadecimal hash string
    """
    # Normalize by sorting keys and converting to JSON
    normalized = json.dumps(summary, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@lru_cache(maxsize=128)
def get_cached_interpretation(summary_hash: str) -> Optional[str]:
    """
    Get cached interpretation if available.
    
    Args:
        summary_hash: SHA256 hash of summary
        
    Returns:
        Cached interpretation text or None
    """
    return _interpretation_cache.get(summary_hash)


def store_cached_interpretation(summary_hash: str, interpretation: str) -> None:
    """
    Store interpretation in cache.
    
    Args:
        summary_hash: SHA256 hash of summary
        interpretation: Interpretation text to cache
    """
    _interpretation_cache[summary_hash] = interpretation
    # Clear LRU cache to ensure fresh lookups
    get_cached_interpretation.cache_clear()


def clear_cache() -> None:
    """Clear all cached interpretations."""
    global _interpretation_cache
    _interpretation_cache.clear()
    get_cached_interpretation.cache_clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache stats
    """
    return {
        "cached_items": len(_interpretation_cache),
        "cache_hits": get_cached_interpretation.cache_info().hits,
        "cache_misses": get_cached_interpretation.cache_info().misses,
        "max_size": get_cached_interpretation.cache_info().maxsize
    }

