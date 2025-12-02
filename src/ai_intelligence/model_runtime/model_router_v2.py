"""
Model Router V2 - Enhanced hybrid routing with domain-specific models
"""

import os
import logging
from typing import Optional, str
from src.local_llm.model_router import ModelRouter
from src.local_llm.openai_client import OpenAIClient
from src.local_llm.groq_client import GroqClient
from src.ai_intelligence.model_runtime.model_loader import GlobalModelPool

logger = logging.getLogger(__name__)


class ModelRouterV2:
    """Enhanced model router with domain-specific routing."""
    
    def __init__(self):
        self.base_router = ModelRouter()
        self.openai_client = OpenAIClient()
        self.groq_client = GroqClient()
    
    def run(
        self,
        prompt: str,
        mode: str = "default",
        use_local_first: bool = True,
        max_tokens: int = 512
    ) -> str:
        """
        Route prompt to best model based on task type.
        
        Args:
            prompt: Input prompt
            mode: Task mode (extraction, mechanism, safety, causal, default)
            use_local_first: Try local model first
            max_tokens: Maximum tokens to generate
        
        Returns:
            Model response
        """
        # Short prompts → local model
        if len(prompt) < 300 and mode in ["extraction", "summary"] and use_local_first:
            try:
                from src.local_llm.config import get_model_config
                config = get_model_config()
                model_name = config.get("reasoning", config.get("summary"))
                model, tokenizer = GlobalModelPool.get(model_name, "reasoning")
                
                if model and tokenizer:
                    return self._run_local(model, tokenizer, prompt, max_tokens)
            except Exception as e:
                logger.debug(f"Local model failed, falling back: {e}")
        
        # Mechanism reasoning → use cloud (better accuracy)
        if mode == "mechanism":
            if self.groq_client.is_available():
                result = self.groq_client.run(prompt, model="llama-3.1-70b-versatile")
                if result:
                    return result
            
            if self.openai_client.is_available():
                result = self.openai_client.run(prompt, model="gpt-4o-mini")
                if result:
                    return result
        
        # Safety/clinical reasoning → use medical-tuned model if available
        if mode == "safety":
            if self.openai_client.is_available():
                # Try GPT-4o-mini first (faster, cheaper)
                result = self.openai_client.run(prompt, model="gpt-4o-mini")
                if result:
                    return result
        
        # Causal reasoning → use best available
        if mode == "causal":
            if self.openai_client.is_available():
                result = self.openai_client.run(prompt, model="gpt-4o-mini")
                if result:
                    return result
        
        # Default: use base router
        return self.base_router.run(prompt, mode=mode)
    
    def _run_local(self, model, tokenizer, prompt: str, max_tokens: int) -> Optional[str]:
        """Run local model inference."""
        try:
            import torch
            from src.local_llm.config import get_device
            
            device = get_device()
            
            # Format prompt
            if hasattr(tokenizer, "apply_chat_template"):
                messages = [{"role": "user", "content": prompt}]
                formatted_prompt = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                formatted_prompt = prompt
            
            # Tokenize
            inputs = tokenizer(formatted_prompt, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id if tokenizer.pad_token_id is None else tokenizer.pad_token_id
                )
            
            # Decode
            response = tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )
            return response.strip()
            
        except Exception as e:
            logger.warning(f"Local inference error: {e}")
            return None

