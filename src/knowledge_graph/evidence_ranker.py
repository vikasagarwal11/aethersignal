"""
Evidence Ranker - Unified Evidence Ranking (Quantum + Causal + Mechanistic + Toxicology)
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EvidenceRanker:
    """
    Unified Evidence Ranking:
    Score = weighted sum of:
    - causal_score
    - fusion_score
    - mechanistic evidence
    - toxicology match
    - novelty bonus
    - quantum hazard score (if available)
    """
    
    def __init__(
        self,
        causal_weight: float = 0.35,
        fusion_weight: float = 0.35,
        tox_weight: float = 0.10,
        novelty_weight: float = 0.10,
        quantum_weight: float = 0.10
    ):
        """
        Initialize evidence ranker with weights.
        
        Args:
            causal_weight: Weight for causal score
            fusion_weight: Weight for fusion score
            tox_weight: Weight for toxicology match
            novelty_weight: Weight for novelty bonus
            quantum_weight: Weight for quantum score
        """
        self.causal_weight = causal_weight
        self.fusion_weight = fusion_weight
        self.tox_weight = tox_weight
        self.novelty_weight = novelty_weight
        self.quantum_weight = quantum_weight
    
    def rank(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rank evidence from complete analysis.
        
        Args:
            analysis: Complete analysis dictionary from MechanismSupervisor
        
        Returns:
            Ranking dictionary with evidence score and breakdown
        """
        # Extract scores
        causal = analysis.get("causal", {}).get("causal_score", 0.0)
        fusion = analysis.get("fusion", {}).get("fusion_score", 0.0)
        tox = 1.0 if analysis.get("toxicology", {}).get("tox_present", False) else 0.0
        novel = 1.0 if analysis.get("novel", False) else 0.0
        quantum = analysis.get("quantum_score", 0.0)
        
        # Calculate weighted score
        score = (
            self.causal_weight * causal +
            self.fusion_weight * fusion +
            self.tox_weight * tox +
            self.novelty_weight * novel +
            self.quantum_weight * quantum
        )
        
        # Ensure score is in [0, 1]
        score = max(0.0, min(1.0, score))
        
        # Determine evidence level
        if score >= 0.8:
            evidence_level = "STRONG"
        elif score >= 0.6:
            evidence_level = "MODERATE"
        elif score >= 0.4:
            evidence_level = "WEAK"
        else:
            evidence_level = "INSUFFICIENT"
        
        return {
            "evidence_score": float(score),
            "evidence_level": evidence_level,
            "breakdown": {
                "causal": float(causal),
                "fusion": float(fusion),
                "toxicity": float(tox),
                "novelty": float(novel),
                "quantum": float(quantum)
            },
            "weights": {
                "causal": self.causal_weight,
                "fusion": self.fusion_weight,
                "toxicity": self.tox_weight,
                "novelty": self.novelty_weight,
                "quantum": self.quantum_weight
            }
        }
    
    def rank_batch(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank multiple analyses.
        
        Args:
            analyses: List of analysis dictionaries
        
        Returns:
            List of ranked analyses sorted by evidence score
        """
        ranked = []
        
        for analysis in analyses:
            ranking = self.rank(analysis)
            combined = {
                **analysis,
                "ranking": ranking
            }
            ranked.append(combined)
        
        # Sort by evidence score (highest first)
        ranked.sort(key=lambda x: x["ranking"]["evidence_score"], reverse=True)
        
        return ranked
    
    def get_top_ranked(self, analyses: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get top K ranked analyses.
        
        Args:
            analyses: List of analysis dictionaries
            top_k: Number of top results
        
        Returns:
            Top K ranked analyses
        """
        ranked = self.rank_batch(analyses)
        return ranked[:top_k]

