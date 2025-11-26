"""
Medical LLM Integration for AetherSignal
Provides unified interface for medical-specialized LLM models.

Supports:
- OpenAI (GPT-4o-mini, GPT-4o) - Primary, cost-effective
- Claude (Opus, Sonnet) - Best for causal reasoning
- BioGPT/Palmyra-Med - Best for biomedical literature
- Extensible architecture for future models
"""

from typing import Dict, Optional, List, Any
import os
import json


def get_available_models() -> Dict[str, List[str]]:
    """
    Get list of available models based on API keys.
    
    Returns:
        Dictionary mapping provider to available models
    """
    available = {}
    
    # Check OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        available["openai"] = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
    
    # Check Anthropic (Claude)
    if os.environ.get("ANTHROPIC_API_KEY"):
        available["anthropic"] = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
    
    # Check Groq (fast inference, not BioGPT)
    if os.environ.get("GROQ_API_KEY"):
        available["groq"] = ["llama-3.1-70b-versatile", "mixtral-8x7b"]
    
    # Check Hugging Face (for BioGPT and other models)
    if os.environ.get("HUGGINGFACEHUB_API_TOKEN") or os.environ.get("HF_API_KEY"):
        available["huggingface"] = ["microsoft/biogpt", "microsoft/BioGPT-Large"]
    
    # Check Writer (Palmyra-Med)
    if os.environ.get("WRITER_API_KEY"):
        available["writer"] = ["palmyra-med-70b"]
    
    # Check xAI (Grok)
    if os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"):
        available["xai"] = ["grok-2-1212", "grok-beta", "grok-2-vision-1212"]
    
    return available


def call_medical_llm(
    prompt: str,
    system_prompt: str,
    task_type: str = "general",
    preferred_model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.3
) -> Optional[str]:
    """
    Unified interface for calling medical LLM models.
    
    Task-specific model selection:
    - "literature": BioGPT/Palmyra-Med preferred, OpenAI fallback
    - "causal_reasoning": Claude Opus preferred, GPT-4o fallback
    - "narrative_analysis": GPT-4o preferred, GPT-4o-mini fallback
    - "meddra_mapping": GPT-4o-mini (cost-effective)
    - "general": GPT-4o-mini (default)
    
    Args:
        prompt: User prompt
        system_prompt: System prompt
        task_type: Type of task (affects model selection)
        preferred_model: Override model selection (format: "provider:model")
        max_tokens: Maximum tokens to generate
        temperature: Temperature (0-1)
        
    Returns:
        Generated text or None if all models fail
    """
    available = get_available_models()
    
    # Determine model priority based on task
    if task_type == "causal_reasoning":
        # Best: Claude Opus, Fallback: GPT-4o, GPT-4o-mini
        model_chain = [
            ("anthropic", "claude-3-opus"),
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
        ]
    elif task_type == "literature":
        # Best: Palmyra-Med, BioGPT (via Hugging Face), Grok, Fallback: GPT-4o, GPT-4o-mini
        model_chain = [
            ("writer", "palmyra-med-70b"),
            ("huggingface", "microsoft/biogpt"),  # BioGPT via Hugging Face
            ("xai", "grok-2-1212"),  # Grok for literature
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
        ]
    elif task_type == "narrative_analysis":
        # Best: GPT-4o, Fallback: GPT-4o-mini, Claude Sonnet
        model_chain = [
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-sonnet"),
        ]
    else:
        # General: GPT-4o-mini (cost-effective)
        model_chain = [
            ("openai", "gpt-4o-mini"),
            ("openai", "gpt-4o"),
        ]
    
    # Override if preferred_model specified
    if preferred_model:
        provider, model = preferred_model.split(":", 1)
        model_chain = [(provider, model)] + [m for m in model_chain if m != (provider, model)]
    
    # Try each model in priority order
    for provider, model in model_chain:
        if provider not in available or model not in available[provider]:
            continue
        
        try:
            if provider == "openai":
                result = _call_openai(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "anthropic":
                result = _call_anthropic(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "groq":
                result = _call_groq(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "writer":
                result = _call_writer(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "xai":
                result = _call_xai(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "huggingface":
                result = _call_huggingface(prompt, system_prompt, model, max_tokens, temperature)
            else:
                continue
            
            if result:
                return result
        except Exception:
            continue  # Try next model
    
    return None


def _call_openai(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=30.0)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    except Exception:
        return None


def _call_anthropic(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Anthropic (Claude) API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, timeout=60.0)
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        return response.content[0].text if response.content else None
    except Exception:
        return None


def _call_groq(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Groq API (for BioGPT alternatives)."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key, timeout=30.0)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    except Exception:
        return None


def _call_writer(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Writer API (Palmyra-Med)."""
    api_key = os.environ.get("WRITER_API_KEY")
    if not api_key:
        return None
    
    try:
        import requests
        
        # Writer API endpoint (example - adjust based on actual API)
        url = "https://api.writer.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        pass
    
    return None


def _call_xai(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call xAI (Grok) API."""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        return None
    
    try:
        import requests
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        pass
    
    return None


def _call_huggingface(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Hugging Face Inference API (for BioGPT and other models)."""
    api_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN") or os.environ.get("HF_API_KEY")
    if not api_token:
        return None
    
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=api_token, timeout=30.0)
        
        # Combine system prompt and user prompt
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Use text generation for BioGPT
        response = client.text_generation(
            full_prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
            return_full_text=False  # Don't repeat the prompt
        )
        
        return response.strip() if response else None
    except Exception:
        # Fallback: try requests-based API if huggingface_hub not available
        try:
            import requests
            
            url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "inputs": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    return result.get("generated_text", "").strip()
        except Exception:
            pass
    
    return None

