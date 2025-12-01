"""
AI Narrative Writer (Phase 3I.3)
Uses Safety Copilot to generate regulatory narratives.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AINarrativeWriter:
    """
    AI-powered narrative writer for regulatory reports.
    """
    
    def __init__(self):
        """Initialize AI narrative writer."""
        pass
    
    def write_signal_summary(
        self,
        drug: str,
        reaction: str,
        signal_data: Dict[str, Any]
    ) -> str:
        """
        Write signal summary narrative.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            signal_data: Signal analysis data
        
        Returns:
            Narrative text
        """
        try:
            from src.ai.medical_llm import call_medical_llm
            
            prompt = self._build_signal_summary_prompt(drug, reaction, signal_data)
            
            # Call medical LLM (adjust parameters based on actual API)
            narrative = call_medical_llm(
                prompt=prompt,
                system_prompt="You are a pharmacovigilance expert writing regulatory signal summaries.",
                task_type="general"
            )
            
            return narrative if narrative else self._fallback_summary(drug, reaction, signal_data)
        except Exception as e:
            logger.error(f"Error generating AI narrative: {str(e)}")
            return self._fallback_summary(drug, reaction, signal_data)
    
    def write_benefit_risk_assessment(
        self,
        drug: str,
        benefit_data: Dict[str, Any],
        risk_data: Dict[str, Any]
    ) -> str:
        """
        Write benefit-risk assessment narrative.
        
        Args:
            drug: Drug name
            benefit_data: Benefit information
            risk_data: Risk information
        
        Returns:
            Narrative text
        """
        try:
            from src.ai.medical_llm import call_medical_llm
            
            prompt = f"""
Write a benefit-risk assessment for {drug}.

Benefits:
{benefit_data}

Risks:
{risk_data}

Provide a balanced, regulatory-appropriate assessment in 3-4 paragraphs.
"""
            
            narrative = call_medical_llm(
                prompt=prompt,
                system_prompt="You are a pharmacovigilance expert writing benefit-risk assessments for regulatory submissions.",
                task_type="general"
            )
            
            return narrative if narrative else "Benefit-risk assessment pending."
        except Exception as e:
            logger.error(f"Error generating benefit-risk narrative: {str(e)}")
            return "Benefit-risk assessment pending."
    
    def write_mechanistic_justification(
        self,
        drug: str,
        reaction: str,
        mechanism_data: Dict[str, Any]
    ) -> str:
        """
        Write mechanistic justification narrative.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            mechanism_data: Mechanism analysis data
        
        Returns:
            Narrative text
        """
        chain = mechanism_data.get("chain", [])
        plausibility = mechanism_data.get("plausibility_score", 0.0)
        
        if chain:
            chain_text = "\n".join(f"- {step}" for step in chain)
            return (
                f"Mechanistic Plausibility: {plausibility:.2f}\n\n"
                f"Mechanistic Chain:\n{chain_text}"
            )
        else:
            return f"Mechanistic plausibility score: {plausibility:.2f}. Detailed mechanism analysis pending."
    
    def _build_signal_summary_prompt(
        self,
        drug: str,
        reaction: str,
        signal_data: Dict[str, Any]
    ) -> str:
        """Build prompt for signal summary."""
        quantum_score = signal_data.get("quantum_score", 0.0)
        gri_score = signal_data.get("gri_score", 0.0)
        sources = signal_data.get("sources", [])
        total_cases = signal_data.get("total_cases", 0)
        
        return f"""
Write a regulatory signal summary for {drug} → {reaction}.

Signal Metrics:
- Quantum Score: {quantum_score:.2f}
- Global Risk Index: {gri_score:.2f}
- Total Cases: {total_cases}
- Sources: {', '.join(sources) if sources else 'Multiple sources'}

Provide a concise, regulatory-appropriate summary (2-3 paragraphs) suitable for PSUR/Signal Evaluation Report.
"""
    
    def _fallback_summary(
        self,
        drug: str,
        reaction: str,
        signal_data: Dict[str, Any]
    ) -> str:
        """Fallback summary if AI unavailable."""
        quantum_score = signal_data.get("quantum_score", 0.0)
        gri_score = signal_data.get("gri_score", 0.0)
        total_cases = signal_data.get("total_cases", 0)
        
        return (
            f"Signal: {drug} → {reaction}\n"
            f"Quantum Score: {quantum_score:.2f}\n"
            f"Global Risk Index: {gri_score:.2f}\n"
            f"Total Cases: {total_cases}\n"
            f"Evidence from multiple sources."
        )

