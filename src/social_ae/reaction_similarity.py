"""
Reaction Similarity Search
Semantic similarity search using embeddings and vector store.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import create_client
    import os
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available, similarity search will use in-memory only")


class ReactionSimilarityEngine:
    """
    Semantic similarity search for reactions using embeddings.
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize similarity engine.
        
        Args:
            supabase_client: Optional Supabase client (for vector store)
        """
        self.supabase = supabase_client
        self._in_memory_store: List[Dict] = []  # Fallback in-memory store
    
    def find_similar_reactions(
        self,
        embedding: np.ndarray,
        k: int = 5,
        drug: Optional[str] = None,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Find similar reactions using embedding similarity.
        
        Args:
            embedding: Query embedding vector
            k: Number of results
            drug: Optional drug filter
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of similar reactions with similarity scores
        """
        if self.supabase and SUPABASE_AVAILABLE:
            return self._supabase_search(embedding, k, drug, min_similarity)
        else:
            return self._in_memory_search(embedding, k, drug, min_similarity)
    
    def _supabase_search(
        self,
        embedding: np.ndarray,
        k: int,
        drug: Optional[str],
        min_similarity: float
    ) -> List[Dict]:
        """Search using Supabase vector store."""
        try:
            # Call RPC function
            response = self.supabase.rpc(
                "find_similar_reactions",
                {
                    "query_embedding": embedding.tolist(),
                    "match_count": k * 2,  # Get more, filter by similarity
                    "drug_filter": drug if drug else None
                }
            ).execute()
            
            # Filter by min_similarity
            results = [
                r for r in response.data
                if r.get("similarity", 0) >= min_similarity
            ][:k]
            
            return results
        except Exception as e:
            logger.warning(f"Supabase similarity search error: {str(e)}")
            return self._in_memory_search(embedding, k, drug, min_similarity)
    
    def _in_memory_search(
        self,
        embedding: np.ndarray,
        k: int,
        drug: Optional[str],
        min_similarity: float
    ) -> List[Dict]:
        """Search using in-memory store (fallback)."""
        if not self._in_memory_store:
            return []
        
        similarities = []
        for item in self._in_memory_store:
            # Filter by drug if specified
            if drug and item.get("drug", "").lower() != drug.lower():
                continue
            
            # Calculate cosine similarity
            item_embedding = np.array(item.get("embedding", []))
            if len(item_embedding) != len(embedding):
                continue
            
            similarity = self._cosine_similarity(embedding, item_embedding)
            if similarity >= min_similarity:
                similarities.append({
                    "reaction_raw": item.get("reaction_raw", ""),
                    "reaction_norm": item.get("reaction_norm", ""),
                    "drug": item.get("drug", ""),
                    "similarity": similarity
                })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def add_to_store(
        self,
        reaction_raw: str,
        reaction_norm: str,
        embedding: np.ndarray,
        drug: Optional[str] = None,
        source: str = "social"
    ):
        """
        Add reaction to vector store.
        
        Args:
            reaction_raw: Raw reaction text
            reaction_norm: Normalized PT
            embedding: Embedding vector
            drug: Drug name
            source: Source name
        """
        if self.supabase and SUPABASE_AVAILABLE:
            try:
                self.supabase.table("reaction_vectors").insert({
                    "reaction_raw": reaction_raw,
                    "reaction_norm": reaction_norm,
                    "drug": drug or "",
                    "embedding": embedding.tolist(),
                    "source": source
                }).execute()
            except Exception as e:
                logger.warning(f"Error adding to Supabase: {str(e)}")
                # Fallback to in-memory
                self._in_memory_store.append({
                    "reaction_raw": reaction_raw,
                    "reaction_norm": reaction_norm,
                    "drug": drug or "",
                    "embedding": embedding.tolist(),
                    "source": source
                })
        else:
            # Use in-memory store
            self._in_memory_store.append({
                "reaction_raw": reaction_raw,
                "reaction_norm": reaction_norm,
                "drug": drug or "",
                "embedding": embedding.tolist(),
                "source": source
            })

