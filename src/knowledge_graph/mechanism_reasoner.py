"""
Mechanism Reasoner - LLM-powered mechanistic reasoning
"""

import os
from typing import Dict, Any, List, Optional
from .kg_router import KGRouter
from .kg_core import KnowledgeGraph
import logging

logger = logging.getLogger(__name__)


class MechanismReasoner:
    """
    Combines:
    - Knowledge Graph chain
    - LLM mechanistic reasoning
    - Literature evidence
    """
    
    def __init__(self, kg: KnowledgeGraph, router: KGRouter):
        self.kg = kg
        self.router = router
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for mechanistic reasoning."""
        try:
            from src.local_llm.model_router import ModelRouter
            router = ModelRouter()
            return router.run(prompt, mode="mechanism")
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return "Mechanistic reasoning unavailable."
    
    def generate_chain(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Generate complete mechanistic chain.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Complete mechanistic explanation
        """
        # Get KG path
        kg_result = self.router.explain(drug, reaction)
        
        # Build LLM prompt
        kg_path_str = " → ".join(kg_result["mechanistic_path"]) if kg_result["mechanistic_path"] else "No path found"
        
        llm_prompt = f"""
Explain the biological mechanism linking drug '{drug}' and reaction '{reaction}'.

Use real pathways, receptors, and drug classes when possible.

Knowledge Graph Path: {kg_path_str}

Provide a detailed biological explanation including:
1. Drug target/receptor
2. Pathway affected
3. Biological cascade leading to the reaction
4. Supporting evidence level

Keep it concise (200-300 words) and scientifically accurate.
        """
        
        llm_explanation = self._call_llm(llm_prompt)
        
        return {
            "drug": drug,
            "reaction": reaction,
            "kg_path": kg_result["mechanistic_path"],
            "path_details": kg_result.get("path_details", []),
            "llm_reasoning": llm_explanation,
            "confidence": self._calculate_confidence(kg_result),
            "all_paths": kg_result.get("all_paths", [])
        }
    
    def _calculate_confidence(self, kg_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on KG path quality."""
        if not kg_result.get("path_found"):
            return 0.0
        
        path = kg_result.get("mechanistic_path", [])
        if not path:
            return 0.0
        
        # Base confidence from path existence
        confidence = 0.5
        
        # Boost for shorter paths (more direct)
        if len(path) <= 3:
            confidence += 0.2
        
        # Boost for multiple paths
        all_paths_count = kg_result.get("all_paths_count", 0)
        if all_paths_count > 1:
            confidence += min(0.2, all_paths_count * 0.05)
        
        # Boost for path details
        path_details = kg_result.get("path_details", [])
        if path_details:
            # Check for high-weight edges
            high_weight_count = sum(1 for p in path_details if p.get("weight", 0) > 1.0)
            if high_weight_count > 0:
                confidence += min(0.1, high_weight_count * 0.05)
        
        return min(1.0, confidence)

