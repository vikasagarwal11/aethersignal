"""
Signal Confidence Score (SCS) Engine (CHUNK 6.21.1 - Part 20)
Bayesian multi-factor confidence score estimating probability that a detected signal represents a real safety risk.
"""
import datetime
from typing import Dict, List, Any, Optional
import numpy as np

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from .shmi_engine import SHMIEngine
    SHMI_AVAILABLE = True
except ImportError:
    SHMI_AVAILABLE = False


class SignalConfidenceEngine:
    """
    Computes Signal Confidence Score (SCS) - a Bayesian weighted model
    combining evidence strength, reproducibility, consistency, narrative support,
    temporal reliability, clinical plausibility, external corroboration, and governance quality.
    
    SCS ranges from 0-100, representing the confidence that a detected signal
    represents a true, meaningful, clinically-valid safety risk.
    """

    def __init__(self):
        """Initialize the Signal Confidence Engine."""
        if SHMI_AVAILABLE:
            self.shmi_engine = SHMIEngine()

    def compute_signal_confidence(self, signal: Dict[str, Any],
                                 signal_stats: Optional[Dict[str, Any]] = None,
                                 trend_alerts: Optional[Any] = None,
                                 narratives: Optional[Dict[str, Any]] = None,
                                 governance_package: Optional[Dict[str, Any]] = None,
                                 external_sources: Optional[Dict[str, Any]] = None,
                                 rpf_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Compute complete Signal Confidence Score using Bayesian combination.
        
        Args:
            signal: Signal dictionary
            signal_stats: Statistical analysis results
            trend_alerts: Trend alerts output
            narratives: Narrative analysis results
            governance_package: Complete governance package
            external_sources: External data source correlations (FAERS, VigiBase, etc.)
            rpf_score: Pre-computed RPF score
            
        Returns:
            Dictionary with SCS score, component likelihoods, and narrative
        """
        components = {}
        
        # 1. Disproportionality component (PRR/ROR)
        components["disproportionality"] = self._compute_disproportionality_likelihood(signal, signal_stats)
        
        # 2. ROR component (separate from PRR)
        components["ror"] = self._compute_ror_likelihood(signal, signal_stats)
        
        # 3. Trend strength component
        components["trend_strength"] = self._compute_trend_strength_likelihood(signal, trend_alerts, signal_stats)
        
        # 4. Subgroup reproducibility component
        components["subgroup_reproducibility"] = self._compute_subgroup_reproducibility_likelihood(signal)
        
        # 5. Narrative support component
        components["narrative_support"] = self._compute_narrative_support_likelihood(signal, narratives)
        
        # 6. Temporal pattern component (seasonality, consistency)
        components["temporal_pattern"] = self._compute_temporal_pattern_likelihood(signal, trend_alerts, signal_stats)
        
        # 7. Clinical plausibility component
        components["clinical_plausibility"] = self._compute_clinical_plausibility_likelihood(signal, governance_package)
        
        # 8. External corroboration component
        components["external_support"] = self._compute_external_support_likelihood(signal, external_sources)
        
        # 9. Governance score component (from SHMI)
        components["governance_score"] = self._compute_governance_likelihood(signal, governance_package)
        
        # Bayesian combination: Posterior = 1 - Π(1 - component_likelihood)
        posterior = 1.0
        for likelihood in components.values():
            posterior *= (1.0 - likelihood)
        posterior = 1.0 - posterior
        
        # Convert to 0-100 score
        scs_score = round(posterior * 100, 2)
        scs_score = max(0, min(100, scs_score))
        
        # Generate AI explanation
        narrative = self._explain_signal_confidence(scs_score, components, signal)
        
        # Categorize confidence level
        confidence_level = self._categorize_confidence(scs_score)
        
        return {
            "scs_score": scs_score,
            "confidence_level": confidence_level,
            "posterior": round(posterior, 4),
            "components": {k: round(v, 4) for k, v in components.items()},
            "narrative": narrative,
            "computed_at": datetime.datetime.utcnow().isoformat()
        }

    def _compute_disproportionality_likelihood(self, signal: Dict[str, Any],
                                              signal_stats: Optional[Dict[str, Any]]) -> float:
        """
        Compute PRR-based disproportionality likelihood (0-1).
        
        PRR >= 2.0 is typically considered a signal threshold.
        """
        prr = signal.get("prr", signal.get("PRR", 1))
        
        if prr is None or prr <= 1:
            return 0.1  # No disproportionality
        
        # Normalize: PRR of 2.0 = 0.5 likelihood, PRR of 4.0+ = 1.0 likelihood
        likelihood = min(prr / 4.0, 1.0)
        
        # Also check confidence intervals if available
        if signal_stats:
            ci_lower = signal_stats.get("prr_ci_lower", signal_stats.get("ci_lower", 1))
            if ci_lower > 1:
                # Stronger confidence if CI excludes 1
                likelihood = min(likelihood * 1.2, 1.0)
        
        return max(0, min(1, likelihood))

    def _compute_ror_likelihood(self, signal: Dict[str, Any],
                               signal_stats: Optional[Dict[str, Any]]) -> float:
        """
        Compute ROR-based likelihood (0-1).
        
        ROR >= 2.0 is typically considered a signal threshold.
        """
        ror = signal.get("ror", signal.get("ROR", 1))
        
        if ror is None or ror <= 1:
            return 0.1
        
        # Normalize: ROR of 2.0 = 0.5 likelihood, ROR of 4.0+ = 1.0 likelihood
        likelihood = min(ror / 4.0, 1.0)
        
        # Check confidence intervals
        if signal_stats:
            ci_lower = signal_stats.get("ror_ci_lower", signal_stats.get("ci_lower", 1))
            if ci_lower > 1:
                likelihood = min(likelihood * 1.2, 1.0)
        
        return max(0, min(1, likelihood))

    def _compute_trend_strength_likelihood(self, signal: Dict[str, Any],
                                          trend_alerts: Optional[Any],
                                          signal_stats: Optional[Dict[str, Any]]) -> float:
        """
        Compute trend strength likelihood based on temporal patterns.
        """
        # Check for trend alerts
        if trend_alerts:
            alerts_list = trend_alerts.get("alerts", []) if isinstance(trend_alerts, dict) else []
            if alerts_list:
                # Count high-severity alerts
                critical_count = sum(1 for a in alerts_list if isinstance(a, dict) and a.get("severity") == "critical")
                high_count = sum(1 for a in alerts_list if isinstance(a, dict) and a.get("severity") == "high")
                
                if critical_count > 0:
                    return 0.9  # Strong trend signal
                elif high_count >= 2:
                    return 0.7  # Moderate-strong trend
                elif high_count == 1:
                    return 0.5  # Moderate trend
                else:
                    return 0.3  # Weak trend
        
        # Check signal_stats for trend indicators
        if signal_stats:
            trend_stability = signal_stats.get("trend_stability", 0)
            if trend_stability > 0.7:
                return 0.7
            elif trend_stability > 0.5:
                return 0.5
            elif trend_stability > 0.3:
                return 0.3
        
        # Default moderate if no trend data
        return 0.4

    def _compute_subgroup_reproducibility_likelihood(self, signal: Dict[str, Any]) -> float:
        """
        Compute subgroup reproducibility likelihood (0-1).
        
        Higher likelihood if signal appears across multiple subgroups.
        """
        subgroups = signal.get("subgroups", signal.get("subgroup_analysis", {}))
        
        if not subgroups:
            return 0.2  # No subgroup analysis
        
        if isinstance(subgroups, dict):
            # Count subgroups with significant signals
            significant_subgroups = 0
            total_subgroups = len(subgroups)
            
            for subgroup_data in subgroups.values():
                if isinstance(subgroup_data, dict):
                    prr = subgroup_data.get("prr", 0)
                    ror = subgroup_data.get("ror", 0)
                    if prr >= 1.5 or ror >= 1.5:
                        significant_subgroups += 1
            
            if total_subgroups > 0:
                reproducibility = significant_subgroups / total_subgroups
                # Boost if multiple subgroups confirm
                if significant_subgroups >= 3:
                    return min(reproducibility * 1.3, 1.0)
                elif significant_subgroups >= 2:
                    return min(reproducibility * 1.2, 1.0)
                else:
                    return reproducibility
        
        # If subgroups analyzed but structure unknown
        return 0.5

    def _compute_narrative_support_likelihood(self, signal: Dict[str, Any],
                                             narratives: Optional[Dict[str, Any]]) -> float:
        """
        Compute narrative support likelihood (0-1).
        
        Higher likelihood if case narratives provide clinical support.
        """
        # Check for narrative data
        case_narratives = signal.get("narratives", signal.get("case_narratives", []))
        
        if case_narratives and len(case_narratives) > 0:
            # Multiple narratives increase confidence
            if len(case_narratives) >= 5:
                return 1.0  # Strong narrative support
            elif len(case_narratives) >= 3:
                return 0.8
            elif len(case_narratives) >= 2:
                return 0.6
            else:
                return 0.4
        
        # Check narratives dict for clinical support flags
        if narratives:
            has_clinical_support = narratives.get("has_clinical_support", False)
            if has_clinical_support:
                return 0.9
        
        # Check if narrative analysis was done
        if signal.get("narrative_analysis") or signal.get("narrative_clusters"):
            return 0.5  # Moderate support
        
        return 0.2  # Weak or no narrative support

    def _compute_temporal_pattern_likelihood(self, signal: Dict[str, Any],
                                            trend_alerts: Optional[Any],
                                            signal_stats: Optional[Dict[str, Any]]) -> float:
        """
        Compute temporal pattern likelihood (seasonality, consistency over time).
        """
        # Check for temporal consistency in trend_alerts
        if trend_alerts:
            alerts_list = trend_alerts.get("alerts", []) if isinstance(trend_alerts, dict) else []
            if alerts_list:
                # Check if alerts are consistent across multiple time periods
                periods = set()
                for alert in alerts_list:
                    if isinstance(alert, dict):
                        period = alert.get("period", alert.get("time_window", ""))
                        if period:
                            periods.add(period)
                
                if len(periods) >= 3:
                    return 0.9  # Consistent across multiple periods
                elif len(periods) >= 2:
                    return 0.7  # Moderate consistency
                elif len(periods) == 1:
                    return 0.5  # Single period
        
        # Check signal_stats for temporal metrics
        if signal_stats:
            temporal_consistency = signal_stats.get("temporal_consistency", 0)
            if temporal_consistency > 0.7:
                return 0.8
            elif temporal_consistency > 0.5:
                return 0.6
        
        # Default moderate
        return 0.4

    def _compute_clinical_plausibility_likelihood(self, signal: Dict[str, Any],
                                                  governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Compute clinical plausibility likelihood (0-1).
        
        Based on clinical relevance assessment, biological mechanism, etc.
        """
        # Check for clinical relevance flag
        clinical_relevance = signal.get("clinical_relevance", "")
        if clinical_relevance and "relevant" in str(clinical_relevance).lower():
            return 0.8
        
        # Check LLM explanation for clinical plausibility
        llm_explanation = signal.get("llm_explanation", {})
        if isinstance(llm_explanation, dict):
            if llm_explanation.get("clinical_relevance") or llm_explanation.get("plausible_mechanism"):
                return 0.7
        
        # Check governance package
        if governance_package:
            clinical_assessment = governance_package.get("clinical_assessment", "")
            if clinical_assessment:
                return 0.6
        
        # Check if biological mechanism mentioned
        rationale = signal.get("rationale", "")
        if rationale and any(term in rationale.lower() for term in ["mechanism", "plausible", "biologically"]):
            return 0.5
        
        return 0.3  # Default low-moderate

    def _compute_external_support_likelihood(self, signal: Dict[str, Any],
                                            external_sources: Optional[Dict[str, Any]]) -> float:
        """
        Compute external corroboration likelihood (FAERS, VigiBase, literature).
        """
        if not external_sources:
            return 0.2  # No external data
        
        # Check FAERS overlap
        faers_overlap = external_sources.get("faers_overlap", False)
        faers_similarity = external_sources.get("faers_similarity", 0)
        
        if faers_overlap and faers_similarity > 0.7:
            return 0.9  # Strong external support
        elif faers_overlap and faers_similarity > 0.5:
            return 0.7
        
        # Check VigiBase
        vigibase_support = external_sources.get("vigibase_support", False)
        if vigibase_support:
            return 0.8
        
        # Check literature
        literature_support = external_sources.get("literature_support", False)
        if literature_support:
            return 0.6
        
        return 0.2  # No external support

    def _compute_governance_likelihood(self, signal: Dict[str, Any],
                                      governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Compute governance score likelihood (0-1) based on SHMI or governance completeness.
        """
        # Try to get SHMI score
        if SHMI_AVAILABLE and self.shmi_engine and governance_package:
            try:
                shmi_result = governance_package.get("shmi", {})
                if isinstance(shmi_result, dict) and "shmi_score" in shmi_result:
                    shmi_score = shmi_result.get("shmi_score", 0)
                    return shmi_score / 100.0
            except:
                pass
        
        # Fallback: use governance completeness
        compliance_score = signal.get("governance_score", signal.get("compliance_score", 0))
        if compliance_score:
            return compliance_score / 100.0
        
        # Check if governance package has completeness indicators
        if governance_package:
            required_sections = ["trends", "risk_profile", "compliance", "reviewer_assignment"]
            present_sections = sum(1 for section in required_sections if governance_package.get(section))
            completeness = present_sections / len(required_sections)
            return completeness
        
        return 0.5  # Default moderate governance

    def _categorize_confidence(self, scs_score: float) -> str:
        """Categorize SCS score into confidence levels."""
        if scs_score >= 80:
            return "Very High Confidence"
        elif scs_score >= 65:
            return "High Confidence"
        elif scs_score >= 50:
            return "Moderate–High Confidence"
        elif scs_score >= 35:
            return "Moderate Confidence"
        elif scs_score >= 20:
            return "Low–Moderate Confidence"
        else:
            return "Low Confidence"

    def _explain_signal_confidence(self, scs_score: float,
                                   components: Dict[str, float],
                                   signal: Dict[str, Any]) -> str:
        """
        Generate AI-powered explanation of Signal Confidence Score.
        
        Args:
            scs_score: SCS score (0-100)
            components: Component likelihoods dictionary
            signal: Signal dictionary
            
        Returns:
            Narrative explanation text
        """
        if not LLM_AVAILABLE:
            # Fallback explanation
            top_components = sorted(components.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join([f"{k} ({v:.2f})" for k, v in top_components])
            
            return (
                f"Signal Confidence Score: {scs_score:.1f}/100 ({self._categorize_confidence(scs_score)}). "
                f"Top contributing factors: {top_str}. "
                f"This score represents the estimated probability that the detected signal represents "
                f"a true, meaningful, clinically-valid safety risk versus noise, confounders, or data quality issues."
            )
        
        drug = signal.get("drug", "the drug")
        reaction = signal.get("reaction", signal.get("event", "the reaction"))
        
        # Format component breakdown
        component_str = "\n".join([f"- {k}: {v:.3f}" for k, v in sorted(components.items(), key=lambda x: x[1], reverse=True)])
        
        prompt = f"""
You are a pharmacovigilance inspector explaining the Signal Confidence Score (SCS) for {drug} - {reaction}.

Overall SCS Score: {scs_score:.1f}/100
Confidence Level: {self._categorize_confidence(scs_score)}

Component Likelihoods (0-1, where 1 = maximum confidence):
{component_str}

Provide:
1. Plain-language interpretation of what this score means
2. Evidence supporting the confidence level
3. Key contributing factors (strongest evidence)
4. Reasons to be cautious (potential limitations, biases, confounders)
5. Risk of false signal or data quality issues
6. What next steps should be taken based on this confidence level
7. Regulatory considerations for signals at this confidence level

Format as a professional regulatory narrative suitable for signal assessment documentation and audit review.
"""
        
        try:
            system_prompt = "You are a pharmacovigilance expert providing Bayesian signal confidence assessments for regulatory signal evaluation."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=1500,
                temperature=0.3
            ) or self._explain_signal_confidence.__doc__  # Fallback
        except Exception as e:
            return f"SCS narrative generation error: {str(e)}"

