"""
Signal Health Maturity Index (SHMI) Engine (CHUNK 6.21.1 - Part 18)
Composite score measuring the health and maturity of safety signals end-to-end.
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
    from .governance_engine import GovernanceEngine
    from .risk_prioritization import RiskPrioritizationEngine
    from .sop_compliance_engine import SOPComplianceEngine
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class SHMIEngine:
    """
    Computes Signal Health Maturity Index (SHMI) - a 0-100 composite score
    reflecting signal quality, governance completeness, SOP compliance,
    reviewer consensus, timeliness, evidence strength, and risk management.
    """

    def __init__(self):
        """Initialize the SHMI Engine."""
        if IMPORTS_AVAILABLE:
            self.governance = GovernanceEngine()
            self.rpf = RiskPrioritizationEngine()
            self.sop_engine = SOPComplianceEngine()

    def compute_shmi(self, signal: Dict[str, Any], 
                    signal_stats: Optional[Dict[str, Any]] = None,
                    trend_alerts: Optional[Any] = None,
                    governance_package: Optional[Dict[str, Any]] = None,
                    reviewer_notes: Optional[List[Dict[str, Any]]] = None,
                    sop_compliance_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Compute complete SHMI score and breakdown.
        
        Args:
            signal: Signal dictionary
            signal_stats: Statistical analysis results
            trend_alerts: Trend alerts output
            governance_package: Complete governance package
            reviewer_notes: List of reviewer notes/decisions
            sop_compliance_score: Pre-computed SOP compliance score (0-100)
            
        Returns:
            Dictionary with SHMI score, breakdown, and narrative
        """
        # A) Evidence Strength Index (0-20)
        evidence_index = self._compute_evidence_strength_index(signal, signal_stats, trend_alerts)
        
        # B) Governance Completeness Index (0-15)
        governance_index = self._compute_governance_completeness_index(governance_package)
        
        # C) SOP Compliance Index (0-15)
        sop_index = self._compute_sop_compliance_index(sop_compliance_score, signal)
        
        # D) Reviewer Consensus Index (0-15)
        reviewer_index = self._compute_reviewer_consensus_index(reviewer_notes)
        
        # E) Timeliness Index (0-10)
        timeliness_index = self._compute_timeliness_index(signal, governance_package)
        
        # F) Risk/Priority Alignment Index (0-10)
        alignment_index = self._compute_priority_alignment_index(signal, governance_package)
        
        # G) Impact & Residual Risk Index (0-15)
        residual_risk_index = self._compute_residual_risk_index(signal, governance_package)
        
        # Total SHMI (clamped 0-100)
        total_shmi = (
            evidence_index + governance_index + sop_index + reviewer_index +
            timeliness_index + alignment_index + residual_risk_index
        )
        total_shmi = max(0, min(100, round(total_shmi, 2)))
        
        # Generate AI narrative
        narrative = self._generate_shmi_narrative(
            total_shmi, evidence_index, governance_index, sop_index,
            reviewer_index, timeliness_index, alignment_index, residual_risk_index,
            signal
        )
        
        # Determine status category
        status = self._categorize_shmi_status(total_shmi)
        
        return {
            "shmi_score": total_shmi,
            "status": status,
            "breakdown": {
                "evidence_strength": round(evidence_index, 2),
                "governance_completeness": round(governance_index, 2),
                "sop_compliance": round(sop_index, 2),
                "reviewer_consensus": round(reviewer_index, 2),
                "timeliness": round(timeliness_index, 2),
                "priority_alignment": round(alignment_index, 2),
                "residual_risk": round(residual_risk_index, 2)
            },
            "narrative": narrative,
            "computed_at": datetime.datetime.utcnow().isoformat()
        }

    def _compute_evidence_strength_index(self, signal: Dict[str, Any],
                                        signal_stats: Optional[Dict[str, Any]],
                                        trend_alerts: Optional[Any]) -> float:
        """
        Evidence Strength Index (0-20).
        
        Measures: PRR/ROR magnitude, stability, reproducibility,
        subgroup consistency, narrative support.
        """
        scores = []
        
        # 1. Signal strength (PRR/ROR magnitude)
        prr = signal.get("prr", signal.get("PRR", 1))
        ror = signal.get("ror", signal.get("ROR", 1))
        disproportionality = max(prr, ror) if (prr > 1 or ror > 1) else 1
        
        if disproportionality >= 4:
            strength_score = 1.0
        elif disproportionality >= 2:
            strength_score = 0.75
        elif disproportionality >= 1.5:
            strength_score = 0.5
        else:
            strength_score = 0.25
        scores.append(strength_score)
        
        # 2. Trend stability (from trend_alerts or signal_stats)
        if signal_stats:
            trend_stability = signal_stats.get("trend_stability", 0)
        elif trend_alerts:
            # Check if trends are stable (no major spikes)
            alerts_list = trend_alerts.get("alerts", []) if isinstance(trend_alerts, dict) else []
            high_severity_count = sum(1 for a in alerts_list if isinstance(a, dict) and a.get("severity") == "critical")
            trend_stability = 1.0 - min(high_severity_count / 5, 1.0)  # Penalize if many critical alerts
        else:
            trend_stability = 0.5  # Default moderate
        
        scores.append(max(0, min(1, trend_stability)))
        
        # 3. Reproducibility (consistency across data sources)
        data_sources = signal.get("data_sources", [])
        if isinstance(data_sources, list) and len(data_sources) > 1:
            reproducibility = 1.0
        elif len(data_sources) == 1:
            reproducibility = 0.7
        else:
            reproducibility = 0.3
        scores.append(reproducibility)
        
        # 4. Subgroup consistency (check if subgroups are present)
        subgroups = signal.get("subgroups", signal.get("subgroup_analysis", {}))
        if subgroups and isinstance(subgroups, dict) and len(subgroups) > 0:
            subgroup_score = 1.0
        elif signal.get("subgroup_analysis_done", False):
            subgroup_score = 0.7
        else:
            subgroup_score = 0.3
        scores.append(subgroup_score)
        
        # 5. Narrative support (case narratives available)
        narratives = signal.get("narratives", signal.get("case_narratives", []))
        if narratives and len(narratives) > 0:
            narrative_score = 1.0
        elif signal.get("narrative_analysis", False):
            narrative_score = 0.7
        else:
            narrative_score = 0.3
        scores.append(narrative_score)
        
        # Average and scale to 0-20
        avg_score = sum(scores) / len(scores) if scores else 0
        return avg_score * 20

    def _compute_governance_completeness_index(self, governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Governance Completeness Index (0-15).
        
        Checks for: trend alerts, RPF, benefit-risk, label impact,
        CAPA, medical assessment, summary narrative.
        """
        if not governance_package:
            return 0.0
        
        required_sections = {
            "trend_alerts": False,
            "rpf": False,
            "benefit_risk": False,
            "label_impact": False,
            "capa": False,
            "medical_assessment": False,
            "summary": False
        }
        
        # Check for trend alerts
        if governance_package.get("trends") or governance_package.get("trend_alerts"):
            required_sections["trend_alerts"] = True
        
        # Check for RPF
        if governance_package.get("risk_profile") or governance_package.get("rpf_score"):
            required_sections["rpf"] = True
        
        # Check for benefit-risk
        if governance_package.get("benefit_risk") or governance_package.get("br_assessment"):
            required_sections["benefit_risk"] = True
        
        # Check for label impact
        if governance_package.get("label_impact") or governance_package.get("label_assessment"):
            required_sections["label_impact"] = True
        
        # Check for CAPA
        if governance_package.get("capa") or governance_package.get("capa_recommendations"):
            required_sections["capa"] = True
        
        # Check for medical assessment
        if governance_package.get("clinical_assessment") or governance_package.get("medical_review"):
            required_sections["medical_assessment"] = True
        
        # Check for summary
        if governance_package.get("ai_summary") or governance_package.get("summary"):
            required_sections["summary"] = True
        
        # Score: each section = 15/7 points
        completed = sum(1 for v in required_sections.values() if v)
        return (completed / len(required_sections)) * 15

    def _compute_sop_compliance_index(self, sop_compliance_score: Optional[float],
                                     signal: Dict[str, Any]) -> float:
        """
        SOP Compliance Index (0-15).
        
        Based on SOP compliance gap score (0-100) → scaled to 0-15.
        """
        if sop_compliance_score is not None:
            return (sop_compliance_score / 100) * 15
        
        # Fallback: check if compliance data exists
        compliance = signal.get("compliance", {})
        if compliance:
            score = compliance.get("score", 0)
            return (score / 100) * 15
        
        return 7.5  # Default moderate score

    def _compute_reviewer_consensus_index(self, reviewer_notes: Optional[List[Dict[str, Any]]]) -> float:
        """
        Reviewer Consensus Index (0-15).
        
        Measures: number of reviewers, agreement level, conflicting interpretations.
        """
        if not reviewer_notes or len(reviewer_notes) == 0:
            return 5.0  # Default if no reviewers
        
        # Count reviewers
        reviewer_count_score = min(len(reviewer_notes) / 3, 1.0) * 5  # Max 3 reviewers = full score
        
        # Check for agreement (simple heuristic)
        decisions = [note.get("decision", note.get("status", "")) for note in reviewer_notes]
        unique_decisions = len(set(decisions))
        
        if len(decisions) == 1:
            agreement_score = 1.0
        elif unique_decisions <= 2 and len(decisions) > 1:
            agreement_score = 0.7  # Mostly agree
        else:
            agreement_score = 0.4  # Disagreement
        
        consensus_score = (reviewer_count_score + (agreement_score * 10))
        return min(consensus_score, 15)

    def _compute_timeliness_index(self, signal: Dict[str, Any],
                                 governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Timeliness Index (0-10).
        
        Penalty-based: late triage, late assessment, missed SLA, delayed assignment.
        """
        score = 10.0
        
        # Check timeline status
        timeline_status = signal.get("timeline_status", {})
        if isinstance(timeline_status, dict):
            assessment_status = timeline_status.get("assessment_status", "")
            if assessment_status == "Severe Delay":
                score -= 5.0
            elif assessment_status == "Moderate Delay":
                score -= 3.0
            elif assessment_status == "Slight Delay":
                score -= 1.5
        
        # Check governance package timeline issues
        if governance_package:
            timeline_guidance = governance_package.get("timeline_guidance", "")
            if "delay" in str(timeline_guidance).lower() or "overdue" in str(timeline_guidance).lower():
                score -= 2.0
        
        return max(0, score)

    def _compute_priority_alignment_index(self, signal: Dict[str, Any],
                                         governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Risk/Priority Alignment Index (0-10).
        
        Measures alignment between RPF priority and signal decision/reviewer justification.
        """
        rpf_score = signal.get("rpf_score", 0)
        priority = signal.get("priority", signal.get("risk_level", "low")).lower()
        lifecycle = signal.get("lifecycle", "").lower()
        
        # Map priority to expected RPF range
        expected_rpf_ranges = {
            "critical": (80, 100),
            "high": (60, 100),
            "medium": (40, 80),
            "low": (0, 60)
        }
        
        expected_range = expected_rpf_ranges.get(priority, (0, 100))
        
        # Check alignment
        if expected_range[0] <= rpf_score <= expected_range[1]:
            alignment_score = 10.0  # Perfect alignment
        elif rpf_score > expected_range[1]:
            # Higher RPF than expected priority - might indicate underestimation
            alignment_score = 6.0
        else:
            # Lower RPF than expected priority
            alignment_score = 7.0
        
        # Check lifecycle alignment
        if priority in ["high", "critical"] and lifecycle not in ["under assessment", "potential risk", "confirmed risk"]:
            alignment_score -= 2.0  # High priority should be in active assessment
        
        return max(0, min(10, alignment_score))

    def _compute_residual_risk_index(self, signal: Dict[str, Any],
                                    governance_package: Optional[Dict[str, Any]]) -> float:
        """
        Impact & Residual Risk Index (0-15).
        
        Evaluates: vulnerable populations, seriousness, hospitalization/fatality,
        residual risk after CAPA, alignment with label risks.
        """
        score = 15.0
        
        # Check seriousness
        serious_cases = signal.get("serious_cases", signal.get("serious_count", 0))
        total_cases = signal.get("cases", signal.get("count", 1))
        if total_cases > 0:
            serious_rate = serious_cases / total_cases
            if serious_rate > 0.5:
                score -= 2.0  # High seriousness reduces residual risk index
            elif serious_rate < 0.1:
                score += 1.0  # Low seriousness increases index
        
        # Check for fatal cases
        fatal_cases = signal.get("fatal_cases", signal.get("fatal_count", 0))
        if fatal_cases > 0:
            score -= 3.0
        
        # Check subgroup analysis (vulnerable populations)
        if not signal.get("subgroups") and not signal.get("subgroup_analysis"):
            score -= 2.0  # Missing subgroup analysis
        
        # Check if CAPA addresses residual risk
        capa = signal.get("capa") or (governance_package.get("capa") if governance_package else None)
        if not capa:
            score -= 3.0  # Missing CAPA increases residual risk
        
        return max(0, min(15, score))

    def _categorize_shmi_status(self, shmi_score: float) -> str:
        """Categorize SHMI score into status levels."""
        if shmi_score >= 80:
            return "Excellent"
        elif shmi_score >= 65:
            return "Good"
        elif shmi_score >= 50:
            return "Moderate - Requires Improvement"
        elif shmi_score >= 35:
            return "Poor - Significant Gaps"
        else:
            return "Critical - Major Issues"

    def _generate_shmi_narrative(self, total_shmi: float,
                                evidence: float, governance: float, sop: float,
                                reviewer: float, timeliness: float,
                                alignment: float, residual: float,
                                signal: Dict[str, Any]) -> str:
        """
        Generate AI-powered narrative explanation of SHMI.
        
        Args:
            total_shmi: Total SHMI score
            evidence, governance, sop, reviewer, timeliness, alignment, residual: Sub-indices
            signal: Signal dictionary
            
        Returns:
            Narrative text
        """
        if not LLM_AVAILABLE:
            # Fallback narrative
            return (
                f"Overall SHMI = {total_shmi:.1f}/100 ({self._categorize_shmi_status(total_shmi)}). "
                f"Evidence strength: {evidence:.1f}/20, Governance completeness: {governance:.1f}/15, "
                f"SOP compliance: {sop:.1f}/15, Reviewer consensus: {reviewer:.1f}/15, "
                f"Timeliness: {timeliness:.1f}/10, Priority alignment: {alignment:.1f}/10, "
                f"Residual risk: {residual:.1f}/15."
            )
        
        drug = signal.get("drug", "the drug")
        reaction = signal.get("reaction", signal.get("event", "the reaction"))
        
        prompt = f"""
You are a pharmacovigilance governance expert.

Explain the Signal Health Maturity Index (SHMI) for {drug} - {reaction}.

Overall SHMI Score: {total_shmi:.1f}/100
Status: {self._categorize_shmi_status(total_shmi)}

Breakdown:
- Evidence Strength: {evidence:.1f}/20
- Governance Completeness: {governance:.1f}/15
- SOP Compliance: {sop:.1f}/15
- Reviewer Consensus: {reviewer:.1f}/15
- Timeliness: {timeliness:.1f}/10
- Priority Alignment: {alignment:.1f}/10
- Residual Risk: {residual:.1f}/15

Provide:
1. Overall assessment (what this score means)
2. Key strengths
3. Key weaknesses or gaps
4. Impact on signal governance quality
5. Recommendations for improvement
6. Inspection readiness assessment

Format as a professional regulatory narrative suitable for executive review and audit documentation.
"""
        
        try:
            system_prompt = "You are a pharmacovigilance governance expert providing signal health assessments for regulatory compliance and inspection readiness."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=1500,
                temperature=0.3
            ) or self._generate_shmi_narrative.__doc__  # Fallback
        except Exception as e:
            return f"SHMI narrative generation error: {str(e)}"

