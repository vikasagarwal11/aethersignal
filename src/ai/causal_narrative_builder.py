"""
Causal Narrative Builder (CHUNK 6.27 - Part F)
Generates FDA/EMA-style regulatory narratives for causal inference results.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


@dataclass
class CausalNarrative:
    """Structured causal narrative for regulatory documents."""
    executive_summary: str
    methods_section: str
    results_section: str
    interpretation_section: str
    regulatory_implications: str
    full_narrative: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "methods_section": self.methods_section,
            "results_section": self.results_section,
            "interpretation_section": self.interpretation_section,
            "regulatory_implications": self.regulatory_implications,
            "full_narrative": self.full_narrative
        }


class CausalNarrativeBuilder:
    """
    Builds regulatory-grade causal inference narratives.
    
    Formats suitable for:
    - DSUR (Development Safety Update Report)
    - PBRER (Periodic Benefit-Risk Evaluation Report)
    - Signal Files
    - Label Impact Assessments
    - Inspector Responses
    """
    
    def __init__(self):
        """Initialize Causal Narrative Builder."""
        pass
    
    def generate_narrative(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str,
        confounders: Optional[List[str]] = None,
        counterfactual_result: Optional[Dict[str, Any]] = None
    ) -> CausalNarrative:
        """
        Generate comprehensive causal narrative.
        
        Args:
            causal_result: Result from CausalInferenceEngine
            drug: Drug name
            reaction: Reaction/event name
            confounders: List of identified confounders
            counterfactual_result: Optional counterfactual simulation results
            
        Returns:
            CausalNarrative with structured sections
        """
        # Build narrative components
        executive_summary = self._generate_executive_summary(
            causal_result, drug, reaction
        )
        
        methods_section = self._generate_methods_section(
            causal_result.get("methods_used", [])
        )
        
        results_section = self._generate_results_section(
            causal_result, counterfactual_result
        )
        
        interpretation_section = self._generate_interpretation(
            causal_result, drug, reaction
        )
        
        regulatory_implications = self._generate_regulatory_implications(
            causal_result
        )
        
        # Combine into full narrative
        full_narrative = self._combine_narrative(
            executive_summary,
            methods_section,
            results_section,
            interpretation_section,
            regulatory_implications
        )
        
        return CausalNarrative(
            executive_summary=executive_summary,
            methods_section=methods_section,
            results_section=results_section,
            interpretation_section=interpretation_section,
            regulatory_implications=regulatory_implications,
            full_narrative=full_narrative
        )
    
    def _generate_executive_summary(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str
    ) -> str:
        """Generate executive summary section."""
        score = causal_result.get("causal_score", 0.0)
        evidence_strength = causal_result.get("evidence_strength", "Weak")
        risk_diff = causal_result.get("risk_difference", 0.0)
        
        if score >= 0.8:
            conclusion = "strong evidence"
            action = "requires immediate regulatory review"
        elif score >= 0.6:
            conclusion = "moderate to strong evidence"
            action = "warrants detailed assessment"
        elif score >= 0.4:
            conclusion = "suggestive evidence"
            action = "requires continued monitoring"
        else:
            conclusion = "weak evidence"
            action = "requires additional data"
        
        summary = f"""Causal inference analysis for {drug} and {reaction} demonstrated {conclusion} of a causal association (causal score: {score:.2%}). 
        The estimated risk difference was {risk_diff:.2%}, suggesting {action}."""
        
        return summary
    
    def _generate_methods_section(self, methods_used: List[str]) -> str:
        """Generate methods section."""
        if not methods_used:
            methods_used = ["Propensity Score Matching", "Inverse Probability Weighting"]
        
        methods_text = "Causal inference was performed using the following methods: "
        methods_text += ", ".join(methods_used[:-1])
        if len(methods_used) > 1:
            methods_text += f", and {methods_used[-1]}."
        else:
            methods_text += methods_used[0] + "."
        
        methods_text += " Propensity scores were estimated using logistic regression, and matching was performed using nearest-neighbor algorithms. Inverse probability weighting was applied to create a pseudo-population where exposure was independent of measured confounders."
        
        return methods_text
    
    def _generate_results_section(
        self,
        causal_result: Dict[str, Any],
        counterfactual_result: Optional[Dict[str, Any]]
    ) -> str:
        """Generate results section."""
        risk_diff = causal_result.get("risk_difference", 0.0)
        risk_ratio = causal_result.get("risk_ratio", 1.0)
        odds_ratio = causal_result.get("odds_ratio", 1.0)
        ci = causal_result.get("confidence_interval")
        
        results = f"""The estimated average treatment effect (risk difference) was {risk_diff:.2%}, 
        corresponding to a risk ratio of {risk_ratio:.2f} and an odds ratio of {odds_ratio:.2f}."""
        
        if ci:
            ci_lower, ci_upper = ci
            results += f" The 95% confidence interval for the risk difference was [{ci_lower:.3f}, {ci_upper:.3f}]."
            if ci_lower > 0:
                results += " This interval excludes zero, supporting a statistically significant causal effect."
        
        if counterfactual_result:
            actual_risk = counterfactual_result.get("actual_risk", 0.0)
            counterfactual_risk = counterfactual_result.get("counterfactual_risk", 0.0)
            results += f" Counterfactual simulation indicated that in the absence of drug exposure, the baseline risk would be {counterfactual_risk:.2%}, compared to the observed risk of {actual_risk:.2%} with exposure."
        
        return results
    
    def _generate_interpretation(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str
    ) -> str:
        """Generate interpretation section."""
        score = causal_result.get("causal_score", 0.0)
        evidence_strength = causal_result.get("evidence_strength", "Weak")
        drivers = causal_result.get("drivers", [])
        confounders = causal_result.get("confounders", [])
        
        interpretation = f"""Based on the {evidence_strength.lower()} evidence strength (causal score: {score:.2%}), 
        there is {evidence_strength.lower()} support for a causal relationship between {drug} exposure and {reaction}."""
        
        if drivers:
            interpretation += f" Key drivers of this association include: {', '.join(drivers[:3])}."
        
        if confounders:
            interpretation += f" The analysis adjusted for potential confounders including: {', '.join(confounders[:3])}."
        
        interpretation += " However, residual confounding cannot be completely ruled out, and additional studies may be warranted to confirm this association."
        
        return interpretation
    
    def _generate_regulatory_implications(
        self,
        causal_result: Dict[str, Any]
    ) -> str:
        """Generate regulatory implications section."""
        score = causal_result.get("causal_score", 0.0)
        
        if score >= 0.8:
            implications = """Given the strong evidence of causality, the following regulatory actions should be considered:
            - Immediate signal assessment and validation
            - Consideration of label updates (Warnings and Precautions section)
            - Enhanced monitoring in post-marketing surveillance
            - Potential communication to health authorities"""
        elif score >= 0.6:
            implications = """Given the moderate to strong evidence, the following actions are recommended:
            - Detailed signal assessment within 30 days
            - Consideration for label updates if additional evidence accumulates
            - Enhanced case collection and monitoring
            - Periodic reassessment of the signal"""
        elif score >= 0.4:
            implications = """Given the suggestive evidence, the following actions are warranted:
            - Continued monitoring of case reports
            - Periodic reassessment of the signal
            - Consideration of targeted case collection
            - Documentation in safety databases"""
        else:
            implications = """Given the weak evidence, the following actions are recommended:
            - Continued monitoring for additional cases
            - Periodic reassessment as new data becomes available
            - Documentation in safety databases for trend analysis"""
        
        return implications
    
    def _combine_narrative(
        self,
        executive: str,
        methods: str,
        results: str,
        interpretation: str,
        implications: str
    ) -> str:
        """Combine all sections into full narrative."""
        full = f"""**Executive Summary**\n\n{executive}\n\n
**Methods**\n\n{methods}\n\n
**Results**\n\n{results}\n\n
**Interpretation**\n\n{interpretation}\n\n
**Regulatory Implications**\n\n{implications}"""
        
        return full
    
    def generate_dsur_section(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str
    ) -> str:
        """Generate DSUR-specific section."""
        narrative = self.generate_narrative(causal_result, drug, reaction)
        return f"""**Emerging Safety Signal: Causal Inference Analysis**

{narrative.executive_summary}

{narrative.results_section}

{narrative.interpretation_section}

This signal will continue to be monitored and assessed in subsequent reporting periods."""
    
    def generate_pbrer_section(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str
    ) -> str:
        """Generate PBRER-specific section."""
        narrative = self.generate_narrative(causal_result, drug, reaction)
        return f"""**New Safety Information: Causal Association Assessment**

{narrative.executive_summary}

{narrative.methods_section}

{narrative.results_section}

{narrative.regulatory_implications}"""
    
    def generate_label_impact_text(
        self,
        causal_result: Dict[str, Any],
        drug: str,
        reaction: str
    ) -> str:
        """Generate label impact assessment text."""
        score = causal_result.get("causal_score", 0.0)
        risk_diff = causal_result.get("risk_difference", 0.0)
        
        if score >= 0.7:
            label_text = f"""Based on causal inference analysis demonstrating strong evidence (causal score: {score:.2%}) 
            of an association between {drug} and {reaction}, consideration should be given to including this adverse event 
            in the Warnings and Precautions section of the product labeling. The estimated risk increase of {risk_diff:.2%} 
            represents a clinically meaningful difference that warrants disclosure to healthcare providers."""
        else:
            label_text = f"""Based on causal inference analysis demonstrating {causal_result.get('evidence_strength', 'weak').lower()} evidence 
            of an association between {drug} and {reaction}, continued monitoring is recommended. At this time, 
            inclusion in product labeling may not be warranted, but the signal should be reassessed as additional data becomes available."""
        
        return label_text


def generate_causal_narrative(
    causal_result: Dict[str, Any],
    drug: str,
    reaction: str,
    confounders: Optional[List[str]] = None,
    counterfactual_result: Optional[Dict[str, Any]] = None
) -> CausalNarrative:
    """
    Convenience function for generating causal narratives.
    
    Args:
        causal_result: Result from CausalInferenceEngine
        drug: Drug name
        reaction: Reaction/event name
        confounders: List of confounders
        counterfactual_result: Optional counterfactual results
        
    Returns:
        CausalNarrative object
    """
    builder = CausalNarrativeBuilder()
    return builder.generate_narrative(
        causal_result, drug, reaction, confounders, counterfactual_result
    )

