"""
GPU Embedding Engine - Large-scale embedding + ANN retrieval
"""

import numpy as np
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GPUEmbeddingEngine:
    """
    GPU-based embedding + FAISS ANN index
    Accelerates:
    - Mechanistic similarity
    - Reaction similarity
    - Cross-source inference
    """
    
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Initialize embedding engine.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.texts = []
        self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            from src.local_llm.config import get_device
            
            device = get_device()
            self.model = SentenceTransformer(self.model_name, device=device)
            logger.info(f"Loaded embedding model: {self.model_name} on {device}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            self.model = None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of text strings
        
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            # Fallback: random embeddings
            return np.random.normal(0, 0.1, size=(len(texts), 384))
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            return np.random.normal(0, 0.1, size=(len(texts), 384))
    
    def build_index(self, texts: List[str], embeddings: Optional[np.ndarray] = None):
        """
        Build FAISS index for fast similarity search.
        
        Args:
            texts: List of text strings
            embeddings: Optional pre-computed embeddings
        """
        try:
            import faiss
        except ImportError:
            logger.warning("FAISS not available, using simple distance search")
            self.texts = texts
            if embeddings is None:
                self.embeddings = self.encode(texts)
            else:
                self.embeddings = embeddings
            return
        
        if embeddings is None:
            embeddings = self.encode(texts)
        
        self.texts = texts
        dim = embeddings.shape[1]
        
        # Create index
        try:
            # Try GPU first
            if faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                cpu_index = faiss.IndexFlatL2(dim)
                self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
                logger.info("Using GPU FAISS index")
            else:
                self.index = faiss.IndexFlatL2(dim)
                logger.info("Using CPU FAISS index")
        except Exception:
            # Fallback to CPU
            self.index = faiss.IndexFlatL2(dim)
            logger.info("Using CPU FAISS index (GPU unavailable)")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        logger.info(f"Built FAISS index with {len(texts)} vectors")
    
    def query(self, text: str, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Query the index for similar texts.
        
        Args:
            text: Query text
            k: Number of results
        
        Returns:
            Tuple of (distances, indices)
        """
        if self.index is None:
            # Fallback to simple distance search
            query_emb = self.encode([text])
            distances = np.linalg.norm(self.embeddings - query_emb, axis=1)
            indices = np.argsort(distances)[:k]
            return distances[indices], indices
        
        query_emb = self.encode([text])
        faiss.normalize_L2(query_emb)
        
        D, I = self.index.search(query_emb.astype('float32'), k)
        return D[0], I[0]
    
    def get_similar_texts(self, text: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Get similar texts with similarity scores.
        
        Args:
            text: Query text
            k: Number of results
        
        Returns:
            List of (text, similarity_score) tuples
        """
        distances, indices = self.query(text, k)
        
        results = []
        for idx, dist in zip(indices, distances):
            if idx < len(self.texts):
                # Convert distance to similarity (1 - normalized distance)
                similarity = 1.0 / (1.0 + dist)
                results.append((self.texts[idx], similarity))
        
        return results

