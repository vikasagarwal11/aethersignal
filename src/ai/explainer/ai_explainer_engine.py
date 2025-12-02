"""
AI Explainer Engine - Wave 5
Medical AI tutor that explains any signal, spike, trend, or reaction
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)


class AIExplainerEngine:
    """
    Central engine for generating AI-powered explanations of safety signals.
    Provides multi-depth explanations: Basic, Intermediate, Advanced.
    """
    
    def __init__(self):
        """Initialize the explainer engine."""
        pass
    
    def explain_signal(
        self,
        drug: str,
        reaction: str,
        evidence: Optional[Dict[str, Any]] = None,
        severity: Optional[float] = None,
        novelty_flag: bool = False,
        depth: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Generate AI explanation for a drug-reaction signal.
        
        Args:
            drug: Drug name
            reaction: Reaction/adverse event name
            evidence: Optional evidence dictionary (FAERS, social, literature counts)
            severity: Optional severity score (0-1)
            novelty_flag: Whether this is a novel signal
            depth: Explanation depth ("basic", "intermediate", "advanced")
        
        Returns:
            Dictionary with explanation text and metadata
        """
        try:
            # Build evidence summary
            evidence_summary = self._build_evidence_summary(evidence)
            
            # Build prompt based on depth
            prompt = self._build_explanation_prompt(
                drug, reaction, evidence_summary, severity, novelty_flag, depth
            )
            
            # Call LLM
            explanation_text = self._call_llm(prompt)
            
            # Parse and structure response
            return self._parse_explanation(explanation_text, depth)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._fallback_explanation(drug, reaction, severity, novelty_flag)
    
    def explain_trend(
        self,
        drug: str,
        reaction: Optional[str],
        trend_data: Dict[str, Any],
        spike_detected: bool = False
    ) -> Dict[str, Any]:
        """
        Explain a trend or spike in adverse events.
        
        Args:
            drug: Drug name
            reaction: Optional reaction name
            trend_data: Trend data dictionary
            spike_detected: Whether a spike was detected
        
        Returns:
            Explanation dictionary
        """
        try:
            prompt = f"""
You are a senior drug safety scientist. Explain this trend:

DRUG: {drug}
REACTION: {reaction or "Multiple reactions"}
SPIKE DETECTED: {spike_detected}

TREND DATA:
{json.dumps(trend_data, indent=2)}

Provide a clear explanation:
1. What the trend shows
2. Why this might be happening
3. What actions a safety team should consider
4. Level of concern (Low/Medium/High)

Keep it concise and actionable.
"""
            
            explanation = self._call_llm(prompt)
            
            return {
                "explanation": explanation,
                "type": "trend",
                "drug": drug,
                "reaction": reaction
            }
            
        except Exception as e:
            logger.error(f"Error explaining trend: {e}")
            return {
                "explanation": f"Trend analysis for {drug} shows {trend_data.get('trend_direction', 'stable')} activity.",
                "type": "trend",
                "error": str(e)
            }
    
    def explain_cluster(
        self,
        cluster_data: Dict[str, Any],
        drug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explain a cluster of similar adverse events.
        
        Args:
            cluster_data: Cluster data dictionary
            drug: Optional drug name
        
        Returns:
            Explanation dictionary
        """
        try:
            prompt = f"""
You are a drug safety scientist. Explain this cluster of adverse events:

CLUSTER SIZE: {cluster_data.get('size', 0)}
DRUG: {drug or 'Multiple drugs'}
EXAMPLES: {json.dumps(cluster_data.get('examples', []), indent=2)}

Explain:
1. What patterns you see in this cluster
2. Potential common mechanism
3. Clinical significance
4. Recommended follow-up actions
"""
            
            explanation = self._call_llm(prompt)
            
            return {
                "explanation": explanation,
                "type": "cluster",
                "cluster_size": cluster_data.get("size", 0)
            }
            
        except Exception as e:
            logger.error(f"Error explaining cluster: {e}")
            return {
                "explanation": f"Cluster of {cluster_data.get('size', 0)} similar adverse events detected.",
                "type": "cluster",
                "error": str(e)
            }
    
    def _build_evidence_summary(self, evidence: Optional[Dict[str, Any]]) -> str:
        """Build human-readable evidence summary."""
        if not evidence:
            return "Limited evidence available."
        
        parts = []
        
        if evidence.get("faers_count", 0) > 0:
            parts.append(f"FAERS: {evidence['faers_count']} reports")
        
        if evidence.get("social_count", 0) > 0:
            parts.append(f"Social Media: {evidence['social_count']} mentions")
        
        if evidence.get("literature_count", 0) > 0:
            parts.append(f"Literature: {evidence['literature_count']} publications")
        
        if evidence.get("clinical_trial_count", 0) > 0:
            parts.append(f"Clinical Trials: {evidence['clinical_trial_count']} cases")
        
        return "; ".join(parts) if parts else "Limited evidence available."
    
    def _build_explanation_prompt(
        self,
        drug: str,
        reaction: str,
        evidence_summary: str,
        severity: Optional[float],
        novelty_flag: bool,
        depth: str
    ) -> str:
        """Build the LLM prompt for explanation."""
        
        severity_text = f"{severity:.2f}" if severity is not None else "Not assessed"
        novelty_text = "Yes - this is a novel signal not previously reported" if novelty_flag else "No - known signal"
        
        depth_instructions = {
            "basic": "Write a simple, non-technical explanation that a non-medical person can understand. Avoid jargon.",
            "intermediate": "Write a clinician-level explanation with medical context and reasoning.",
            "advanced": "Write a detailed pharmacological and mechanistic explanation with hypothesis generation."
        }
        
        depth_instruction = depth_instructions.get(depth, depth_instructions["intermediate"])
        
        prompt = f"""
You are a senior drug safety scientist with expertise in pharmacovigilance and adverse event analysis.

Explain the following safety signal:

DRUG: {drug}
REACTION: {reaction}
SEVERITY SCORE: {severity_text} (0 = mild, 1 = severe)
NOVELTY: {novelty_text}
EVIDENCE: {evidence_summary}

{depth_instruction}

Structure your response as follows:

## Summary
[Brief 2-3 sentence summary]

## Clinical Significance
[What this means clinically]

## Mechanism Hypothesis
[Possible biological/pharmacological mechanisms]

## Level of Concern
[Low/Medium/High with reasoning]

## Recommended Actions
[What a safety team should do next]

Keep the explanation clear, evidence-based, and actionable.
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM for explanation generation.
        Uses ModelRouter with fallback logic.
        """
        try:
            # Try to use ModelRouter if available
            from src.local_llm.model_router import ModelRouter
            router = ModelRouter()
            response = router.run(prompt, mode="reasoning")
            return response
        except Exception:
            try:
                # Fallback to OpenAI if available
                import os
                from openai import OpenAI
                
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a senior drug safety scientist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                # Final fallback
                return f"Explanation generation temporarily unavailable. Please try again later."
    
    def _parse_explanation(self, explanation_text: str, depth: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        return {
            "explanation": explanation_text,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "formatted": True
        }
    
    def _fallback_explanation(
        self,
        drug: str,
        reaction: str,
        severity: Optional[float],
        novelty_flag: bool
    ) -> Dict[str, Any]:
        """Generate fallback explanation when LLM is unavailable."""
        severity_text = f"Severity score: {severity:.2f}" if severity is not None else "Severity not assessed"
        novelty_text = "This is a novel signal requiring investigation." if novelty_flag else "This is a known signal."
        
        return {
            "explanation": f"""
## Summary
Safety signal detected for {drug} associated with {reaction}.

## Clinical Significance
{severity_text}. {novelty_text}

## Recommended Actions
1. Review available evidence
2. Assess causality
3. Consider regulatory reporting if warranted
4. Monitor for additional cases

*Note: Detailed AI explanation temporarily unavailable. Please consult safety databases and literature.*
""",
            "depth": "basic",
            "fallback": True
        }

