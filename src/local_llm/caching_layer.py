"""
Caching Layer - Caches model responses for performance
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of model responses."""
    
    def __init__(self, cache_dir: str = "data/cache/llm"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=24)  # 24 hour cache
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """
        Generate cache key from prompt and model.
        
        Args:
            prompt: Input prompt
            model: Model identifier
        
        Returns:
            Cache key (hash)
        """
        key_string = f"{model}:{prompt}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        """
        Get cached response if available.
        
        Args:
            prompt: Input prompt
            model: Model identifier
        
        Returns:
            Cached response or None
        """
        cache_key = self._get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            
            # Check TTL
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - cached_time > self.default_ttl:
                cache_file.unlink()  # Delete expired cache
                return None
            
            logger.debug(f"Cache hit for {model}")
            return cache_data["response"]
            
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, prompt: str, model: str, response: str):
        """
        Cache a response.
        
        Args:
            prompt: Input prompt
            model: Model identifier
            response: Response to cache
        """
        cache_key = self._get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                "prompt": prompt,
                "model": model,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
            
            logger.debug(f"Cached response for {model}")
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def clear(self, model: Optional[str] = None):
        """
        Clear cache.
        
        Args:
            model: Optional model to clear, or None for all
        """
        if model:
            # Clear specific model cache
            pattern = f"*{model}*.json"
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        
        logger.info(f"Cache cleared for {model or 'all models'}")

