"""
Global Model Pool - Cold-start elimination through model pooling
"""

import threading
import logging
from typing import Optional, Dict, Any
from src.local_llm.local_model_loader import LocalModelLoader

logger = logging.getLogger(__name__)


class GlobalModelPool:
    """Manages a global pool of loaded models to eliminate cold starts."""
    
    _models: Dict[str, Any] = {}
    _tokenizers: Dict[str, Any] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get(cls, model_name: str, model_type: str = "reasoning") -> tuple:
        """
        Get a model from the pool (load if not cached).
        
        Args:
            model_name: Model identifier
            model_type: Type of model (reasoning, summary, embed)
        
        Returns:
            Tuple of (model, tokenizer)
        """
        cache_key = f"{model_type}_{model_name}"
        
        with cls._lock:
            if cache_key in cls._models:
                logger.debug(f"Using cached model: {cache_key}")
                return (
                    cls._models[cache_key],
                    cls._tokenizers[cache_key]
                )
            
            # Load model
            logger.info(f"Loading model into pool: {cache_key}")
            model, tokenizer = LocalModelLoader.load(model_name)
            
            if model and tokenizer:
                cls._models[cache_key] = model
                cls._tokenizers[cache_key] = tokenizer
                logger.info(f"Model {cache_key} loaded into pool")
            
            return model, tokenizer
    
    @classmethod
    def preload(cls, model_configs: Dict[str, str]):
        """
        Preload models into the pool.
        
        Args:
            model_configs: Dictionary mapping model_type to model_name
        """
        logger.info("Preloading models into pool...")
        for model_type, model_name in model_configs.items():
            try:
                cls.get(model_name, model_type)
            except Exception as e:
                logger.warning(f"Failed to preload {model_type}: {e}")
        logger.info("Model preloading complete")
    
    @classmethod
    def clear_pool(cls):
        """Clear the model pool."""
        with cls._lock:
            cls._models.clear()
            cls._tokenizers.clear()
            logger.info("Model pool cleared")
    
    @classmethod
    def get_pool_status(cls) -> Dict[str, Any]:
        """
        Get status of the model pool.
        
        Returns:
            Dictionary with pool statistics
        """
        with cls._lock:
            return {
                "loaded_models": list(cls._models.keys()),
                "model_count": len(cls._models),
                "tokenizer_count": len(cls._tokenizers)
            }

