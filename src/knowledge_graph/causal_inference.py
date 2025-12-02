"""
Causal Inference Engine - Bradford-Hill + KG-based causality assessment
"""

from typing import Dict, Any, List, Optional
from .kg_core import KnowledgeGraph
from .kg_router import KGRouter
import logging

logger = logging.getLogger(__name__)


class CausalInferenceEngine:
    """
    Combines:
    - Knowledge Graph evidence
    - Bradford-Hill criteria
    - Multi-source consensus
    """
    
    def __init__(self, kg: KnowledgeGraph, router: KGRouter):
        self.kg = kg
        self.router = router
    
    def assess_causality(self, drug: str, reaction: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess causality using Bradford-Hill criteria + KG.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            evidence: Evidence dictionary with source data
        
        Returns:
            Causality assessment
        """
        # Get KG path
        kg_explanation = self.router.explain(drug, reaction)
        
        # Bradford-Hill criteria scores
        criteria_scores = {
            "strength": self._assess_strength(evidence),
            "consistency": self._assess_consistency(evidence),
            "specificity": self._assess_specificity(evidence),
            "temporality": self._assess_temporality(evidence),
            "biological_gradient": self._assess_gradient(evidence),
            "plausibility": self._assess_plausibility(kg_explanation),
            "coherence": self._assess_coherence(kg_explanation, evidence),
            "experiment": self._assess_experiment(evidence),
            "analogy": self._assess_analogy(evidence)
        }
        
        # Overall causality score
        overall_score = sum(criteria_scores.values()) / len(criteria_scores)
        
        # Determine causality level
        if overall_score >= 0.8:
            causality_level = "DEFINITE"
        elif overall_score >= 0.6:
            causality_level = "PROBABLE"
        elif overall_score >= 0.4:
            causality_level = "POSSIBLE"
        else:
            causality_level = "UNLIKELY"
        
        return {
            "drug": drug,
            "reaction": reaction,
            "overall_score": overall_score,
            "causality_level": causality_level,
            "criteria_scores": criteria_scores,
            "kg_path": kg_explanation.get("mechanistic_path"),
            "kg_confidence": kg_explanation.get("path_found", False)
        }
    
    def _assess_strength(self, evidence: Dict[str, Any]) -> float:
        """Assess strength of association."""
        faers_count = evidence.get("faers_count", 0)
        social_count = evidence.get("social_count", 0)
        literature_count = evidence.get("literature_count", 0)
        
        total = faers_count + social_count + literature_count
        
        if total >= 100:
            return 1.0
        elif total >= 50:
            return 0.8
        elif total >= 20:
            return 0.6
        elif total >= 10:
            return 0.4
        else:
            return 0.2
    
    def _assess_consistency(self, evidence: Dict[str, Any]) -> float:
        """Assess consistency across sources."""
        sources = []
        if evidence.get("faers_count", 0) > 0:
            sources.append("faers")
        if evidence.get("social_count", 0) > 0:
            sources.append("social")
        if evidence.get("literature_count", 0) > 0:
            sources.append("literature")
        
        if len(sources) >= 3:
            return 1.0
        elif len(sources) == 2:
            return 0.7
        elif len(sources) == 1:
            return 0.4
        else:
            return 0.1
    
    def _assess_specificity(self, evidence: Dict[str, Any]) -> float:
        """Assess specificity of association."""
        # Simplified: check if reaction is specific to this drug class
        return 0.5  # Placeholder
    
    def _assess_temporality(self, evidence: Dict[str, Any]) -> float:
        """Assess temporal relationship."""
        # Check if reaction occurs after drug exposure
        temporal_data = evidence.get("temporal", {})
        if temporal_data.get("consistent", False):
            return 0.8
        else:
            return 0.5
    
    def _assess_gradient(self, evidence: Dict[str, Any]) -> float:
        """Assess dose-response relationship."""
        dose_data = evidence.get("dose_response", {})
        if dose_data.get("positive", False):
            return 0.8
        else:
            return 0.5
    
    def _assess_plausibility(self, kg_explanation: Dict[str, Any]) -> float:
        """Assess biological plausibility from KG."""
        if kg_explanation.get("path_found", False):
            return 0.9
        else:
            return 0.3
    
    def _assess_coherence(self, kg_explanation: Dict[str, Any], evidence: Dict[str, Any]) -> float:
        """Assess coherence with known facts."""
        if kg_explanation.get("path_found", False) and evidence.get("literature_count", 0) > 0:
            return 0.9
        else:
            return 0.5
    
    def _assess_experiment(self, evidence: Dict[str, Any]) -> float:
        """Assess experimental evidence."""
        if evidence.get("experimental", False):
            return 0.9
        else:
            return 0.3
    
    def _assess_analogy(self, evidence: Dict[str, Any]) -> float:
        """Assess analogy to similar cases."""
        similar_cases = evidence.get("similar_cases", 0)
        if similar_cases >= 10:
            return 0.8
        elif similar_cases >= 5:
            return 0.6
        else:
            return 0.4

