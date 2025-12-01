"""
Reaction Embedding Engine
Generates embeddings for reaction terms using OpenAI or fallback vectors.
REUSES existing components where possible.
"""

import numpy as np
from typing import Optional
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ReactionEmbeddingEngine:
    """
    Generates embeddings for reaction terms.
    Uses OpenAI text-embedding-3-small by default, with fallback for offline use.
    """
    
    def __init__(self, model: str = "text-embedding-3-small", dimension: int = 1536):
        """
        Initialize embedding engine.
        
        Args:
            model: OpenAI model name
            dimension: Embedding dimension (1536 for text-embedding-3-small)
        """
        self.model = model
        self.dimension = dimension
        self._openai_available = False
        self._check_openai()
    
    def _check_openai(self):
        """Check if OpenAI is available."""
        try:
            import openai
            import os
            if os.getenv("OPENAI_API_KEY"):
                self._openai_available = True
        except ImportError:
            pass
    
    @lru_cache(maxsize=50000)
    def embed(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector or None
        """
        if not text or not isinstance(text, str) or text.strip() == "":
            return np.zeros(self.dimension)
        
        # Try OpenAI first
        if self._openai_available:
            try:
                import openai
                import os
                
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.embeddings.create(
                    model=self.model,
                    input=text
                )
                return np.array(response.data[0].embedding)
            except Exception as e:
                logger.debug(f"OpenAI embedding error: {str(e)}")
        
        # Fallback: generate stable pseudo-random vector based on text hash
        # This ensures same text always gets same vector (deterministic)
        import hashlib
        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(text_hash % (2**32))
        embedding = np.random.normal(0, 0.001, size=(self.dimension,))
        np.random.seed()  # Reset seed
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        return [self.embed(text) for text in texts]

