"""
LLM Mechanistic Reasoner (Phase 3D.4C)
Uses LLM to generate human-readable mechanistic explanations.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LLMMechanisticReasoner:
    """
    LLM-powered mechanistic reasoning engine.
    """
    
    def __init__(self):
        """Initialize LLM reasoner."""
        pass
    
    def explain_mechanism(
        self,
        drug: str,
        reaction: str,
        chain: List[str],
        targets: List[str],
        pathways: List[str],
        literature_support: Optional[float] = None,
        similar_drugs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate LLM explanation for mechanism.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            chain: Mechanistic chain steps
            targets: Drug targets
            pathways: Associated pathways
            literature_support: Optional literature support score
            similar_drugs: Optional list of similar drugs
        
        Returns:
            Dictionary with explanation and metadata
        """
        try:
            from src.ai.medical_llm import call_medical_llm
            
            # Build prompt
            prompt = self._build_prompt(
                drug, reaction, chain, targets, pathways,
                literature_support, similar_drugs
            )
            
            # Call LLM
            explanation = call_medical_llm(
                prompt=prompt,
                system_prompt="You are a biomedical safety expert explaining drug mechanisms and adverse event causality.",
                task_type="general",
                max_tokens=500,
                temperature=0.3
            )
            
            return {
                "drug": drug,
                "reaction": reaction,
                "explanation": explanation or "Mechanistic explanation unavailable.",
                "confidence": "high" if literature_support and literature_support > 0.7 else "moderate",
                "chain": chain,
                "targets": targets,
                "pathways": pathways
            }
        except Exception as e:
            logger.error(f"Error generating LLM explanation: {str(e)}")
            return {
                "drug": drug,
                "reaction": reaction,
                "explanation": f"Mechanistic chain: {' → '.join(chain)}",
                "confidence": "low",
                "chain": chain,
                "targets": targets,
                "pathways": pathways
            }
    
    def _build_prompt(
        self,
        drug: str,
        reaction: str,
        chain: List[str],
        targets: List[str],
        pathways: List[str],
        literature_support: Optional[float],
        similar_drugs: Optional[List[str]]
    ) -> str:
        """Build LLM prompt for mechanistic explanation."""
        prompt_parts = [
            f"Explain the biological mechanism connecting {drug} → {reaction}.",
            "",
            "Mechanistic chain:",
            "\n".join(f"- {step}" for step in chain),
            "",
            f"Drug targets: {', '.join(targets)}",
            f"Pathways involved: {', '.join(pathways)}",
        ]
        
        if similar_drugs:
            prompt_parts.append(f"Similar drugs with this reaction: {', '.join(similar_drugs)}")
        
        if literature_support:
            prompt_parts.append(f"Literature support: {literature_support:.0%}")
        
        prompt_parts.extend([
            "",
            "Provide a concise, clinically relevant explanation (2-3 sentences) of why this mechanism is plausible.",
            "Focus on biological pathways and physiological effects."
        ])
        
        return "\n".join(prompt_parts)

