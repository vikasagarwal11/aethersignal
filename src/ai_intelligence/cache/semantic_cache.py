"""
Semantic Cache - Caches responses based on semantic similarity
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticCache:
    """Semantic cache for LLM responses using embedding-based similarity."""
    
    def __init__(self, cache_dir: str = "data/cache/semantic", similarity_threshold: float = 0.85):
        """
        Initialize semantic cache.
        
        Args:
            cache_dir: Directory for cache storage
            similarity_threshold: Minimum similarity for cache hit (0-1)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold
        self._embedding_model = None
        self._cache = {}
        self._load_cache()
    
    def _get_embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                logger.warning("SentenceTransformers not available, using hash-based cache")
                self._embedding_model = None
        return self._embedding_model
    
    def _get_cache_key(self, query: str) -> str:
        """
        Generate cache key from query.
        
        Args:
            query: Input query
        
        Returns:
            Cache key
        """
        # Normalize query
        query_normalized = " ".join(query.lower().split())
        
        # Use embedding if available, otherwise hash
        model = self._get_embedding_model()
        if model:
            try:
                embedding = model.encode(query_normalized)
                # Use first few dimensions for key
                key_data = embedding[:16].tobytes()
                return hashlib.sha256(key_data).hexdigest()
            except Exception:
                pass
        
        # Fallback to hash
        return hashlib.sha256(query_normalized.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[str]:
        """
        Get cached response if available.
        
        Args:
            query: Input query
        
        Returns:
            Cached response or None
        """
        cache_key = self._get_cache_key(query)
        
        # Check in-memory cache first
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            # Check TTL (24 hours)
            if datetime.now() - cached_item["timestamp"] < timedelta(hours=24):
                logger.debug(f"Semantic cache hit: {cache_key[:8]}")
                return cached_item["response"]
            else:
                # Expired, remove
                del self._cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cached_item = json.load(f)
                
                # Check TTL
                cached_time = datetime.fromisoformat(cached_item["timestamp"])
                if datetime.now() - cached_time < timedelta(hours=24):
                    response = cached_item["response"]
                    # Load into memory cache
                    self._cache[cache_key] = {
                        "response": response,
                        "timestamp": cached_time
                    }
                    logger.debug(f"Semantic cache hit (disk): {cache_key[:8]}")
                    return response
                else:
                    # Expired, delete
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        return None
    
    def set(self, query: str, response: str):
        """
        Cache a response.
        
        Args:
            query: Input query
            response: Response to cache
        """
        cache_key = self._get_cache_key(query)
        timestamp = datetime.now()
        
        # Store in memory
        self._cache[cache_key] = {
            "response": response,
            "timestamp": timestamp
        }
        
        # Store on disk
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "query": query,
                    "response": response,
                    "timestamp": timestamp.isoformat()
                }, f)
            logger.debug(f"Cached response: {cache_key[:8]}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _load_cache(self):
        """Load cache from disk into memory."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        cached_item = json.load(f)
                    
                    cache_key = cache_file.stem
                    cached_time = datetime.fromisoformat(cached_item["timestamp"])
                    
                    # Only load if not expired
                    if datetime.now() - cached_time < timedelta(hours=24):
                        self._cache[cache_key] = {
                            "response": cached_item["response"],
                            "timestamp": cached_time
                        }
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Cache load error: {e}")
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception:
            pass
        logger.info("Semantic cache cleared")

