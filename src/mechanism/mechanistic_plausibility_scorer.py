"""
Mechanistic Plausibility Scorer (Phase 3D.4D)
Calculates 0-1 plausibility score for drug-AE pairs.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MechanisticPlausibilityScorer:
    """
    Calculates mechanistic plausibility scores.
    """
    
    def __init__(self):
        """Initialize plausibility scorer."""
        self.weights = {
            "target_ae_association": 0.25,
            "pathway_evidence": 0.20,
            "literature_mentions": 0.15,
            "similar_drug_patterns": 0.15,
            "clinical_trial_consistency": 0.10,
            "severity_alignment": 0.05,
            "cluster_proximity": 0.05,
            "novelty_vs_known": 0.05
        }
    
    def calculate_score(
        self,
        drug: str,
        reaction: str,
        target_ae_score: Optional[float] = None,
        pathway_evidence: Optional[float] = None,
        literature_mentions: Optional[float] = None,
        similar_drug_support: Optional[float] = None,
        clinical_support: Optional[float] = None,
        severity_alignment: Optional[float] = None,
        cluster_proximity: Optional[float] = None,
        novelty_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate mechanistic plausibility score.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            target_ae_score: Target-AE association score
            pathway_evidence: Pathway evidence score
            literature_mentions: Literature mention score
            similar_drug_support: Similar drug pattern score
            clinical_support: Clinical trial consistency score
            severity_alignment: Severity alignment score
            cluster_proximity: Cluster proximity score
            novelty_score: Novelty score (inverse - known AEs score higher)
        
        Returns:
            Dictionary with score and component breakdown
        """
        components = {}
        
        # Target-AE association
        components["target_ae_association"] = target_ae_score or self._estimate_target_ae_score(drug, reaction)
        
        # Pathway evidence
        components["pathway_evidence"] = pathway_evidence or self._estimate_pathway_evidence(drug, reaction)
        
        # Literature mentions
        components["literature_mentions"] = literature_mentions or 0.5
        
        # Similar drug patterns
        components["similar_drug_patterns"] = similar_drug_support or self._estimate_similar_drug_support(drug, reaction)
        
        # Clinical trial consistency
        components["clinical_trial_consistency"] = clinical_support or 0.5
        
        # Severity alignment
        components["severity_alignment"] = severity_alignment or 0.5
        
        # Cluster proximity
        components["cluster_proximity"] = cluster_proximity or 0.5
        
        # Novelty (inverse - known AEs are more plausible)
        if novelty_score is not None:
            components["novelty_vs_known"] = 1.0 - novelty_score
        else:
            components["novelty_vs_known"] = 0.7  # Assume moderately known
        
        # Calculate weighted score
        total_score = sum(
            components[dim] * self.weights[dim]
            for dim in self.weights.keys()
        )
        
        total_score = max(0.0, min(1.0, total_score))
        
        return {
            "drug": drug,
            "reaction": reaction,
            "plausibility_score": round(total_score, 3),
            "components": components,
            "category": self._categorize_plausibility(total_score)
        }
    
    def _estimate_target_ae_score(self, drug: str, reaction: str) -> float:
        """Estimate target-AE association score."""
        # Simplified heuristic
        drug_lower = drug.lower()
        reaction_lower = reaction.lower()
        
        # GLP-1 agonists → GI symptoms (high association)
        if any(glp1 in drug_lower for glp1 in ["semaglutide", "liraglutide", "dulaglutide", "mounjaro"]):
            if any(gi in reaction_lower for gi in ["nausea", "vomiting", "diarrhea", "gastric"]):
                return 0.9
        
        # Default moderate
        return 0.5
    
    def _estimate_pathway_evidence(self, drug: str, reaction: str) -> float:
        """Estimate pathway evidence score."""
        # Simplified heuristic
        # In production, would query pathway databases
        return 0.6
    
    def _estimate_similar_drug_support(self, drug: str, reaction: str) -> float:
        """Estimate similar drug pattern support."""
        # Simplified heuristic
        # In production, would check drug class patterns
        return 0.5
    
    def _categorize_plausibility(self, score: float) -> str:
        """Categorize plausibility score."""
        if score >= 0.8:
            return "highly_plausible"
        elif score >= 0.6:
            return "plausible"
        elif score >= 0.4:
            return "moderately_plausible"
        else:
            return "low_plausibility"

