"""
Model Router - Intelligent routing between local and cloud models
"""

import logging
from typing import Optional, Dict, Any
from .config import get_model_config, is_local_enabled, get_device
from .local_model_loader import LocalModelLoader
from .openai_client import OpenAIClient
from .groq_client import GroqClient
from .fallback_manager import FallbackManager
from .caching_layer import CacheManager

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes requests to the best available model."""
    
    def __init__(self):
        self.config = get_model_config()
        self.cache = CacheManager()
        self.fallback = FallbackManager()
        
        # Setup fallback chain
        self.fallback.add_fallback(self._try_groq)
        self.fallback.add_fallback(self._try_openai)
        self.fallback.add_fallback(self._emergency_fallback)
    
    def run(self, prompt: str, mode: str = "general", use_cache: bool = True) -> str:
        """
        Run a prompt through the best available model.
        
        Args:
            prompt: Input prompt
            mode: Mode ("reasoning", "summary", "embed", "general")
            use_cache: Whether to use cache
        
        Returns:
            Model response
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, mode)
            if cached:
                return cached
        
        # Try local model first (if enabled and appropriate)
        if is_local_enabled() and mode in ["reasoning", "summary"]:
            result = self._try_local(prompt, mode)
            if result:
                if use_cache:
                    self.cache.set(prompt, mode, result)
                return result
        
        # Use fallback chain
        result = self.fallback.execute_with_fallback(
            lambda: self._try_local(prompt, mode),
            prompt,
            mode
        )
        
        if result and use_cache:
            self.cache.set(prompt, mode, result)
        
        return result
    
    def _try_local(self, prompt: str, mode: str) -> Optional[str]:
        """Try local model."""
        try:
            model_name = self.config.get(mode, self.config.get("reasoning"))
            model, tokenizer = LocalModelLoader.load(model_name)
            
            if model is None or tokenizer is None:
                return None
            
            # Format prompt
            if "instruct" in model_name.lower():
                formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            else:
                formatted_prompt = prompt
            
            # Tokenize
            inputs = tokenizer(formatted_prompt, return_tensors="pt")
            device = get_device()
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate
            import torch
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode
            response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            return response.strip()
            
        except Exception as e:
            logger.warning(f"Local model failed: {e}")
            return None
    
    def _try_groq(self, prompt: str, mode: str) -> Optional[str]:
        """Try Groq API."""
        if GroqClient.is_available():
            return GroqClient.run(prompt)
        return None
    
    def _try_openai(self, prompt: str, mode: str) -> Optional[str]:
        """Try OpenAI API."""
        if OpenAIClient.is_available():
            return OpenAIClient.run(prompt)
        return None
    
    def _emergency_fallback(self, prompt: str, mode: str) -> str:
        """Emergency fallback when all models fail."""
        return "Unable to process request. Please check your model configuration and API keys."

