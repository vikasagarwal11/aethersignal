"""
Local LLM Configuration - Device detection and model settings
"""

import os
from typing import Dict, Any


def has_gpu() -> bool:
    """
    Check if CUDA GPU is available.
    
    Returns:
        True if CUDA GPU available, False otherwise
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def has_mps() -> bool:
    """
    Check if Apple Silicon (Metal Performance Shaders) is available.
    
    Returns:
        True if MPS available, False otherwise
    """
    try:
        import torch
        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except ImportError:
        return False


def get_device() -> str:
    """
    Get the best available device for model inference.
    
    Returns:
        Device string: "cuda", "mps", or "cpu"
    """
    if has_gpu():
        return "cuda"
    if has_mps():
        return "mps"
    return "cpu"


def get_model_config() -> Dict[str, Any]:
    """
    Get model configuration based on available hardware.
    
    Returns:
        Dictionary with model settings
    """
    device = get_device()
    
    # Model selection based on device
    if device == "cuda":
        # Can use larger models on GPU
        return {
            "reasoning": "meta-llama/Llama-3-8B-Instruct",
            "summary": "mistralai/Mistral-7B-Instruct-v0.2",
            "embed": "nomic-ai/nomic-embed-text-v1",
            "device": device,
            "torch_dtype": "float16",
            "load_in_8bit": False
        }
    elif device == "mps":
        # Apple Silicon - medium models
        return {
            "reasoning": "meta-llama/Llama-3-3B-Instruct",
            "summary": "mistralai/Mistral-7B-Instruct-v0.2",
            "embed": "nomic-ai/nomic-embed-text-v1",
            "device": device,
            "torch_dtype": "float16",
            "load_in_8bit": False
        }
    else:
        # CPU only - smallest models
        return {
            "reasoning": "meta-llama/Llama-3-3B-Instruct",
            "summary": "mistralai/Mistral-7B-Instruct-v0.2",
            "embed": "nomic-ai/nomic-embed-text-v1",
            "device": device,
            "torch_dtype": "float32",
            "load_in_8bit": True  # Use quantization on CPU
        }


def get_api_keys() -> Dict[str, str]:
    """
    Get API keys from environment variables.
    
    Returns:
        Dictionary with API keys
    """
    return {
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "groq": os.getenv("GROQ_API_KEY", ""),
    }


def is_local_enabled() -> bool:
    """
    Check if local models are enabled.
    
    Returns:
        True if local models should be used
    """
    return os.getenv("USE_LOCAL_MODELS", "true").lower() == "true"

