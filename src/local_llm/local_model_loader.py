"""
Local Model Loader - Loads and caches local LLM models
"""

from typing import Tuple, Optional
import logging
from .config import get_model_config, get_device

logger = logging.getLogger(__name__)


class LocalModelLoader:
    """Manages loading and caching of local LLM models."""
    
    _model_cache = {}
    _tokenizer_cache = {}
    
    @staticmethod
    def load(model_name: str, force_reload: bool = False) -> Tuple[Optional[object], Optional[object]]:
        """
        Load a local model and tokenizer.
        
        Args:
            model_name: HuggingFace model identifier
            force_reload: Force reload even if cached
        
        Returns:
            Tuple of (model, tokenizer) or (None, None) if loading fails
        """
        if not force_reload and model_name in LocalModelLoader._model_cache:
            logger.info(f"Using cached model: {model_name}")
            return (
                LocalModelLoader._model_cache[model_name],
                LocalModelLoader._tokenizer_cache[model_name]
            )
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            config = get_model_config()
            device = get_device()
            
            logger.info(f"Loading model {model_name} on {device}...")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=getattr(torch, config.get("torch_dtype", "float32")),
                device_map=device if device != "cpu" else None,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            
            if device == "cpu":
                model = model.to(device)
            
            # Cache models
            LocalModelLoader._model_cache[model_name] = model
            LocalModelLoader._tokenizer_cache[model_name] = tokenizer
            
            logger.info(f"Successfully loaded model: {model_name}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None, None
    
    @staticmethod
    def clear_cache():
        """Clear the model cache."""
        LocalModelLoader._model_cache.clear()
        LocalModelLoader._tokenizer_cache.clear()
        logger.info("Model cache cleared")
    
    @staticmethod
    def is_loaded(model_name: str) -> bool:
        """
        Check if a model is already loaded.
        
        Args:
            model_name: Model identifier
        
        Returns:
            True if model is cached
        """
        return model_name in LocalModelLoader._model_cache

