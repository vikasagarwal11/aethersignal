"""
Mechanistic Caching Layer - Redis + Local Fallback
"""

import os
import json
from typing import Dict, Any, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class MechanismCache:
    """
    Caching layer for mechanistic analysis results.
    Uses Redis if available, falls back to local in-memory cache.
    """
    
    def __init__(self, redis_host: Optional[str] = None, redis_port: int = 6379, redis_db: int = 0):
        """
        Initialize cache.
        
        Args:
            redis_host: Redis host (defaults to env var or localhost)
            redis_port: Redis port
            redis_db: Redis database number
        """
        self.local_cache: Dict[str, Any] = {}
        self.redis = None
        
        if REDIS_AVAILABLE:
            try:
                host = redis_host or os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", redis_port))
                db = int(os.getenv("REDIS_DB", redis_db))
                
                self.redis = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis.ping()
                logger.info(f"Connected to Redis at {host}:{port}")
            except Exception as e:
                logger.warning(f"Redis unavailable, using local cache: {e}")
                self.redis = None
        else:
            logger.info("Redis not installed, using local cache only")
    
    def _key(self, drug: str, reaction: str) -> str:
        """
        Generate cache key.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Cache key
        """
        key_string = f"{drug.lower()}_{reaction.lower()}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, drug: str, reaction: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Cached data or None
        """
        key = self._key(drug, reaction)
        
        # Try Redis first
        if self.redis:
            try:
                cached = self.redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to local cache
        return self.local_cache.get(key)
    
    def set(self, drug: str, reaction: str, data: Dict[str, Any], ttl: int = 86400):
        """
        Cache result.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            data: Data to cache
            ttl: Time to live in seconds (default 24 hours)
        """
        key = self._key(drug, reaction)
        
        # Store in Redis if available
        if self.redis:
            try:
                self.redis.set(key, json.dumps(data), ex=ttl)
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Always store in local cache as backup
        self.local_cache[key] = data
    
    def clear(self):
        """Clear all caches."""
        self.local_cache.clear()
        if self.redis:
            try:
                self.redis.flushdb()
            except Exception as e:
                logger.warning(f"Redis flush error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "local_cache_size": len(self.local_cache),
            "redis_available": self.redis is not None
        }
        
        if self.redis:
            try:
                stats["redis_info"] = self.redis.info("memory")
            except Exception:
                pass
        
        return stats

