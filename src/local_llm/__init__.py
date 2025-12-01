"""
Local LLM Module - Hybrid AI Architecture
Supports local models (LLaMA, Mistral) with OpenAI/Groq fallback
"""

from .model_router import ModelRouter
from .config import has_gpu, has_mps, get_device, get_model_config
from .local_model_loader import LocalModelLoader
from .openai_client import OpenAIClient
from .groq_client import GroqClient
from .fallback_manager import FallbackManager
from .caching_layer import CacheManager
from .vector_store import LocalVectorStore

__all__ = [
    "ModelRouter",
    "has_gpu",
    "has_mps",
    "get_device",
    "get_model_config",
    "LocalModelLoader",
    "OpenAIClient",
    "GroqClient",
    "FallbackManager",
    "CacheManager",
    "LocalVectorStore"
]

