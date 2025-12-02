"""
Mechanism Embedding Fusion - Fuses drug, reaction, and mechanism embeddings
"""

import numpy as np
from typing import Dict, List
from .embeddings_gpu import GPUEmbeddingEngine
import logging

logger = logging.getLogger(__name__)


class MechanismEmbeddingFusion:
    """
    Fuses representations:
    - Drug embeddings
    - Reaction embeddings
    - Mechanism embeddings
    Produces a unified similarity score:
    S = α * sim(drug, reaction) + β * sim(mechanism, reaction)
    """
    
    def __init__(self, model: GPUEmbeddingEngine):
        self.model = model
    
    def fuse(self, drug: str, reaction: str, mech_texts: List[str]) -> Dict[str, float]:
        """
        Fuse drug, reaction, and mechanism embeddings.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            mech_texts: List of mechanism text descriptions
        
        Returns:
            Fusion scores dictionary
        """
        try:
            # Encode embeddings
            drug_emb = self.model.encode([drug])
            reac_emb = self.model.encode([reaction])
            
            if not mech_texts:
                mech_emb = np.zeros((1, drug_emb.shape[1]))
            else:
                mech_emb = self.model.encode(mech_texts)
            
            def sim(a, b):
                """Compute cosine similarity."""
                a_norm = a / (np.linalg.norm(a) + 1e-8)
                b_norm = b / (np.linalg.norm(b) + 1e-8)
                return float(np.dot(a_norm, b_norm.T))
            
            # Compute similarities
            drug_reac_sim = sim(drug_emb[0], reac_emb[0])
            
            # Average mechanism-reaction similarity
            if len(mech_emb) > 0:
                mech_reac_sims = [sim(mech_emb[i], reac_emb[0]) for i in range(len(mech_emb))]
                mech_reac_sim = float(np.mean(mech_reac_sims))
            else:
                mech_reac_sim = 0.0
            
            # Fusion score: weighted combination
            score = 0.6 * drug_reac_sim + 0.4 * mech_reac_sim
            
            return {
                "drug_reaction_similarity": float(drug_reac_sim),
                "mechanism_reaction_similarity": float(mech_reac_sim),
                "fusion_score": float(score)
            }
            
        except Exception as e:
            logger.error(f"Embedding fusion error: {e}")
            return {
                "drug_reaction_similarity": 0.0,
                "mechanism_reaction_similarity": 0.0,
                "fusion_score": 0.0
            }

