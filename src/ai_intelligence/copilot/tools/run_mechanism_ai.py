"""
Mechanism AI Tool - Explain drug-AE mechanisms
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MechanismAITool:
    """Tool for mechanism reasoning."""
    
    name = "mechanism_ai"
    description = "Explain mechanism linking drug and AE"
    
    def run(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Run mechanism AI reasoning.
        
        Args:
            drug: Drug name
            reaction: Adverse event
        
        Returns:
            Mechanism explanation dictionary
        """
        try:
            from src.ai_intelligence.advanced.mechanism_graph import MechanismGraph
            
            graph_engine = MechanismGraph()
            graph = graph_engine.infer_pathway(drug, reaction)
            
            # Try to get real mechanism reasoning if available
            try:
                from src.mechanism.llm_mechanistic_reasoner import LLMMechanisticReasoning
                reasoner = LLMMechanisticReasoning()
                explanation = reasoner.explain_mechanism(drug, reaction)
            except Exception:
                explanation = f"Mechanism pathway: {drug} → {graph.get('target', 'Target')} → {graph.get('pathway', 'Pathway')} → {reaction}"
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "graph": graph,
                "explanation": explanation,
                "summary": f"Mechanism explanation for {drug} → {reaction}"
            }
            
        except Exception as e:
            logger.error(f"Mechanism AI error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "drug": drug,
                "reaction": reaction
            }

