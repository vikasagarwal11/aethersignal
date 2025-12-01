"""
Signal Lifecycle Governance Matrix (SLGM) Engine (CHUNK 6.21.1 - Part 19)
Evaluates signal governance quality across all lifecycle stages.
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
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class LifecycleMatrixEngine:
    """
    Computes Signal Lifecycle Governance Matrix (SLGM) - evaluates signal
    governance quality across 8 lifecycle stages with 8 dimensions each.
    """
    
    STAGES = [
        "detection",
        "validation",
        "prioritization",
        "assessment",
        "recommendation",
        "risk_management",
        "close_out",
        "post_monitoring"
    ]
    
    DIMENSIONS = [
        "timeliness",
        "completeness",
        "evidence_strength",
        "reviewer_actions",
        "consensus",
        "decision_quality",
        "governance_compliance",
        "traceability"
    ]
    
    # Each dimension scored 0-5, each stage max 40 points
    MAX_STAGE_SCORE = 40
    MAX_TOTAL_SCORE = 320  # 8 stages × 40 points

    def __init__(self):
        """Initialize the Lifecycle Matrix Engine."""
        if IMPORTS_AVAILABLE:
            self.governance = GovernanceEngine()
            self.rpf = RiskPrioritizationEngine()

    def compute_lifecycle_matrix(self, signal: Dict[str, Any],
                                signal_stats: Optional[Dict[str, Any]] = None,
                                trend_alerts: Optional[Any] = None,
                                governance_package: Optional[Dict[str, Any]] = None,
                                reviewer_notes: Optional[List[Dict[str, Any]]] = None,
                                sop_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compute complete lifecycle governance matrix.
        
        Args:
            signal: Signal dictionary
            signal_stats: Statistical analysis results
            trend_alerts: Trend alerts output
            governance_package: Complete governance package
            reviewer_notes: List of reviewer notes/decisions
            sop_requirements: SOP requirements dictionary
            
        Returns:
            Dictionary with stage scores, total normalized score, and narratives
        """
        stages = {}
        
        # Score each lifecycle stage
        stages["detection"] = self._score_signal_detection(signal, signal_stats, trend_alerts)
        stages["validation"] = self._score_signal_validation(signal, governance_package, sop_requirements)
        stages["prioritization"] = self._score_signal_prioritization(signal, governance_package)
        stages["assessment"] = self._score_signal_assessment(signal, reviewer_notes, governance_package)
        stages["recommendation"] = self._score_signal_recommendation(signal, governance_package)
        stages["risk_management"] = self._score_risk_management(signal, governance_package, sop_requirements)
        stages["close_out"] = self._score_close_out(signal, governance_package)
        stages["post_monitoring"] = self._score_post_monitoring(signal, governance_package)
        
        # Calculate total raw score and normalize to 0-100
        total_raw = sum(stages.values())
        total_normalized = round((total_raw / self.MAX_TOTAL_SCORE) * 100, 2)
        
        # Generate AI narratives for each stage
        narratives = {}
        for stage_name, stage_score in stages.items():
            narratives[stage_name] = self._generate_stage_narrative(
                stage_name, stage_score, signal, governance_package
            )
        
        # Overall assessment
        status = self._categorize_matrix_status(total_normalized)
        
        return {
            "stage_scores": stages,
            "total_normalized": total_normalized,
            "total_raw": total_raw,
            "max_possible": self.MAX_TOTAL_SCORE,
            "status": status,
            "narratives": narratives,
            "computed_at": datetime.datetime.utcnow().isoformat()
        }

    def _score_signal_detection(self, signal: Dict[str, Any],
                               signal_stats: Optional[Dict[str, Any]],
                               trend_alerts: Optional[Any]) -> float:
        """
        Score Signal Detection stage (0-40).
        
        Dimensions: timeliness, completeness, evidence_strength, reviewer_actions,
        consensus, decision_quality, governance_compliance, traceability
        """
        scores = {}
        
        # Timeliness: Was detection timely?
        detected_date = signal.get("detected_on", signal.get("detected_date"))
        if detected_date:
            scores["timeliness"] = 5.0  # Detection timestamped
        else:
            scores["timeliness"] = 2.0
        
        # Completeness: Detection methods documented?
        detection_method = signal.get("detection_method", "")
        if detection_method:
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.5
        
        # Evidence strength: Statistical strength at detection
        prr = signal.get("prr", signal.get("PRR", 1))
        ror = signal.get("ror", signal.get("ROR", 1))
        disproportionality = max(prr, ror) if (prr > 1 or ror > 1) else 1
        
        if disproportionality >= 2:
            scores["evidence_strength"] = 5.0
        elif disproportionality >= 1.5:
            scores["evidence_strength"] = 3.5
        else:
            scores["evidence_strength"] = 2.0
        
        # Reviewer actions: N/A for detection (auto-detected)
        scores["reviewer_actions"] = 5.0  # Automated detection is acceptable
        
        # Consensus: N/A for detection
        scores["consensus"] = 5.0
        
        # Decision quality: Was detection decision appropriate?
        if disproportionality >= 1.5 or signal.get("cases", 0) >= 3:
            scores["decision_quality"] = 5.0
        else:
            scores["decision_quality"] = 3.0
        
        # Governance compliance: Alignment with detection SOPs
        if signal.get("detection_method") or signal.get("statistical_method"):
            scores["governance_compliance"] = 5.0
        else:
            scores["governance_compliance"] = 3.0
        
        # Traceability: Detection logged?
        if detected_date:
            scores["traceability"] = 5.0
        else:
            scores["traceability"] = 2.0
        
        return sum(scores.values())

    def _score_signal_validation(self, signal: Dict[str, Any],
                                governance_package: Optional[Dict[str, Any]],
                                sop_requirements: Optional[Dict[str, Any]]) -> float:
        """Score Signal Validation stage (0-40)."""
        scores = {}
        
        # Timeliness: Validation within timeline?
        validated_date = signal.get("validated_date")
        detected_date = signal.get("detected_on")
        
        if validated_date and detected_date:
            # Check if within 30 days
            try:
                validated = datetime.datetime.fromisoformat(str(validated_date).replace('Z', '+00:00'))
                detected = datetime.datetime.fromisoformat(str(detected_date).replace('Z', '+00:00'))
                days_diff = (validated - detected).days
                if days_diff <= 30:
                    scores["timeliness"] = 5.0
                elif days_diff <= 45:
                    scores["timeliness"] = 3.5
                else:
                    scores["timeliness"] = 2.0
            except:
                scores["timeliness"] = 3.0
        else:
            scores["timeliness"] = 2.0
        
        # Completeness: Validation rationale present?
        if signal.get("validated") or validated_date or signal.get("lifecycle") in ["Validated Signal", "Under Assessment"]:
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.0
        
        # Evidence strength: Clinical plausibility assessed?
        if signal.get("clinical_relevance") or signal.get("llm_explanation"):
            scores["evidence_strength"] = 5.0
        else:
            scores["evidence_strength"] = 2.5
        
        # Reviewer actions: Reviewer assigned?
        if signal.get("assigned_to") or signal.get("reviewer"):
            scores["reviewer_actions"] = 5.0
        else:
            scores["reviewer_actions"] = 2.0
        
        # Consensus: N/A for validation (usually single reviewer)
        scores["consensus"] = 5.0
        
        # Decision quality: Validation decision justified?
        if signal.get("rationale") or signal.get("validation_rationale"):
            scores["decision_quality"] = 5.0
        else:
            scores["decision_quality"] = 2.5
        
        # Governance compliance: SOP followed?
        scores["governance_compliance"] = 4.0  # Default moderate
        
        # Traceability: Validation logged?
        if validated_date:
            scores["traceability"] = 5.0
        else:
            scores["traceability"] = 2.0
        
        return sum(scores.values())

    def _score_signal_prioritization(self, signal: Dict[str, Any],
                                    governance_package: Optional[Dict[str, Any]]) -> float:
        """Score Signal Prioritization stage (0-40)."""
        scores = {}
        
        # Timeliness: Prioritization done promptly?
        scores["timeliness"] = 4.0  # Default
        
        # Completeness: RPF or priority score present?
        if signal.get("rpf_score") is not None or signal.get("priority"):
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.0
        
        # Evidence strength: Priority justified by evidence?
        rpf_score = signal.get("rpf_score", 0)
        priority = signal.get("priority", "")
        if rpf_score > 0 and priority:
            scores["evidence_strength"] = 5.0
        else:
            scores["evidence_strength"] = 2.5
        
        # Reviewer actions: Reviewer involved in prioritization?
        if signal.get("assigned_to"):
            scores["reviewer_actions"] = 5.0
        else:
            scores["reviewer_actions"] = 2.5
        
        # Consensus: Priority agreed upon?
        scores["consensus"] = 4.0  # Default moderate
        
        # Decision quality: Priority appropriate?
        if rpf_score >= 60 and priority in ["High", "high", "Critical", "critical"]:
            scores["decision_quality"] = 5.0
        elif rpf_score < 40 and priority in ["Low", "low"]:
            scores["decision_quality"] = 5.0
        else:
            scores["decision_quality"] = 3.5
        
        # Governance compliance: RPF methodology used?
        if governance_package and governance_package.get("risk_profile"):
            scores["governance_compliance"] = 5.0
        else:
            scores["governance_compliance"] = 3.0
        
        # Traceability: Prioritization logged?
        scores["traceability"] = 4.0  # Default moderate
        
        return sum(scores.values())

    def _score_signal_assessment(self, signal: Dict[str, Any],
                                reviewer_notes: Optional[List[Dict[str, Any]]],
                                governance_package: Optional[Dict[str, Any]]) -> float:
        """Score Signal Assessment stage (0-40)."""
        scores = {}
        
        # Timeliness: Assessment completed on time?
        timeline_status = signal.get("timeline_status", {})
        if isinstance(timeline_status, dict):
            assessment_status = timeline_status.get("assessment_status", "")
            if assessment_status == "On Time":
                scores["timeliness"] = 5.0
            elif assessment_status in ["Slight Delay", "Moderate Delay"]:
                scores["timeliness"] = 3.0
            else:
                scores["timeliness"] = 2.0
        else:
            scores["timeliness"] = 3.0
        
        # Completeness: Assessment includes all required sections?
        required = ["rationale", "clinical_relevance", "trend_analysis"]
        completed = sum(1 for req in required if signal.get(req) or (governance_package and governance_package.get(req)))
        scores["completeness"] = (completed / len(required)) * 5
        
        # Evidence strength: Strong clinical/statistical evidence reviewed?
        if signal.get("llm_explanation") or signal.get("clinical_assessment"):
            scores["evidence_strength"] = 5.0
        else:
            scores["evidence_strength"] = 3.0
        
        # Reviewer actions: Multiple reviewers involved?
        if reviewer_notes and len(reviewer_notes) >= 2:
            scores["reviewer_actions"] = 5.0
        elif reviewer_notes and len(reviewer_notes) == 1:
            scores["reviewer_actions"] = 3.5
        else:
            scores["reviewer_actions"] = 2.0
        
        # Consensus: Reviewer agreement level
        if reviewer_notes:
            decisions = [note.get("decision", "") for note in reviewer_notes]
            unique_decisions = len(set(decisions))
            if unique_decisions == 1:
                scores["consensus"] = 5.0
            elif unique_decisions <= 2:
                scores["consensus"] = 3.5
            else:
                scores["consensus"] = 2.0
        else:
            scores["consensus"] = 3.0
        
        # Decision quality: Assessment decision clinically reasonable?
        if signal.get("rationale") and signal.get("clinical_relevance"):
            scores["decision_quality"] = 5.0
        else:
            scores["decision_quality"] = 3.0
        
        # Governance compliance: Assessment follows SOPs?
        scores["governance_compliance"] = 4.0
        
        # Traceability: Assessment logged?
        scores["traceability"] = 4.5
        
        return sum(scores.values())

    def _score_signal_recommendation(self, signal: Dict[str, Any],
                                    governance_package: Optional[Dict[str, Any]]) -> float:
        """Score Signal Recommendation stage (0-40)."""
        scores = {}
        
        # Timeliness: Recommendation provided promptly?
        scores["timeliness"] = 4.0
        
        # Completeness: Recommendation includes next steps?
        if signal.get("next_steps") or signal.get("recommended_actions") or (governance_package and governance_package.get("followup_plan")):
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.0
        
        # Evidence strength: Recommendation based on evidence?
        if signal.get("rationale") and signal.get("next_steps"):
            scores["evidence_strength"] = 5.0
        else:
            scores["evidence_strength"] = 3.0
        
        # Reviewer actions: Recommendation reviewed?
        scores["reviewer_actions"] = 4.0
        
        # Consensus: Recommendation agreed upon?
        scores["consensus"] = 4.0
        
        # Decision quality: Recommendation appropriate?
        scores["decision_quality"] = 4.0
        
        # Governance compliance: Recommendation aligns with governance?
        scores["governance_compliance"] = 4.0
        
        # Traceability: Recommendation logged?
        scores["traceability"] = 4.0
        
        return sum(scores.values())

    def _score_risk_management(self, signal: Dict[str, Any],
                              governance_package: Optional[Dict[str, Any]],
                              sop_requirements: Optional[Dict[str, Any]]) -> float:
        """Score Risk Management stage (0-40)."""
        scores = {}
        
        # Timeliness: Risk management actions taken promptly?
        scores["timeliness"] = 4.0
        
        # Completeness: CAPA and risk minimization present?
        has_capa = signal.get("capa") or (governance_package and governance_package.get("capa_recommendations"))
        has_risk_min = signal.get("risk_minimization") or governance_package and governance_package.get("risk_minimization")
        
        if has_capa and has_risk_min:
            scores["completeness"] = 5.0
        elif has_capa or has_risk_min:
            scores["completeness"] = 3.5
        else:
            scores["completeness"] = 2.0
        
        # Evidence strength: Risk management based on evidence?
        scores["evidence_strength"] = 4.0
        
        # Reviewer actions: Risk management reviewed?
        scores["reviewer_actions"] = 4.0
        
        # Consensus: Risk management approach agreed?
        scores["consensus"] = 4.0
        
        # Decision quality: Risk management appropriate?
        scores["decision_quality"] = 4.0
        
        # Governance compliance: Aligns with GVP Module IX?
        scores["governance_compliance"] = 4.0
        
        # Traceability: Risk management logged?
        scores["traceability"] = 4.0
        
        return sum(scores.values())

    def _score_close_out(self, signal: Dict[str, Any],
                        governance_package: Optional[Dict[str, Any]]) -> float:
        """Score Close-Out stage (0-40)."""
        scores = {}
        
        # Timeliness: Close-out completed on time?
        if signal.get("closed") or signal.get("status") in ["Closed", "Archived"]:
            scores["timeliness"] = 5.0
        else:
            scores["timeliness"] = 3.0
        
        # Completeness: Close-out rationale documented?
        if signal.get("decision_rationale") or signal.get("closure_rationale"):
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.5
        
        # Evidence strength: Close-out justified?
        scores["evidence_strength"] = 4.0
        
        # Reviewer actions: Close-out approved?
        scores["reviewer_actions"] = 4.5
        
        # Consensus: Close-out agreed?
        scores["consensus"] = 4.0
        
        # Decision quality: Close-out appropriate?
        scores["decision_quality"] = 4.0
        
        # Governance compliance: Close-out follows SOPs?
        scores["governance_compliance"] = 4.0
        
        # Traceability: Close-out fully logged?
        if signal.get("closed_date") or signal.get("closure_date"):
            scores["traceability"] = 5.0
        else:
            scores["traceability"] = 3.0
        
        return sum(scores.values())

    def _score_post_monitoring(self, signal: Dict[str, Any],
                              governance_package: Optional[Dict[str, Any]]) -> float:
        """Score Post-Monitoring stage (0-40)."""
        scores = {}
        
        # Timeliness: Monitoring plan active?
        scores["timeliness"] = 4.0
        
        # Completeness: Monitoring plan documented?
        if signal.get("monitoring_plan") or signal.get("post_closure_monitoring"):
            scores["completeness"] = 5.0
        else:
            scores["completeness"] = 2.0
        
        # Evidence strength: Monitoring based on risk?
        scores["evidence_strength"] = 4.0
        
        # Reviewer actions: Monitoring assigned?
        scores["reviewer_actions"] = 4.0
        
        # Consensus: Monitoring approach agreed?
        scores["consensus"] = 4.0
        
        # Decision quality: Monitoring appropriate?
        scores["decision_quality"] = 4.0
        
        # Governance compliance: Monitoring follows SOPs?
        scores["governance_compliance"] = 4.0
        
        # Traceability: Monitoring logged?
        scores["traceability"] = 4.0
        
        return sum(scores.values())

    def _categorize_matrix_status(self, normalized_score: float) -> str:
        """Categorize lifecycle matrix score into status levels."""
        if normalized_score >= 80:
            return "Excellent"
        elif normalized_score >= 65:
            return "Good"
        elif normalized_score >= 50:
            return "Moderate - Requires Improvement"
        elif normalized_score >= 35:
            return "Poor - Significant Gaps"
        else:
            return "Critical - Major Issues"

    def _generate_stage_narrative(self, stage_name: str, stage_score: float,
                                  signal: Dict[str, Any],
                                  governance_package: Optional[Dict[str, Any]]) -> str:
        """Generate AI-powered narrative for a lifecycle stage."""
        if not LLM_AVAILABLE:
            return f"Stage: {stage_name}, Score: {stage_score}/40. Detailed narrative unavailable without LLM."
        
        stage_display = stage_name.replace("_", " ").title()
        drug = signal.get("drug", "the drug")
        reaction = signal.get("reaction", signal.get("event", "the reaction"))
        
        prompt = f"""
You are a pharmacovigilance inspector evaluating the {stage_display} lifecycle stage for {drug} - {reaction}.

Stage Score: {stage_score}/40
Normalized Score: {round((stage_score / 40) * 100, 1)}/100

Provide:
1. Plain-language explanation of the stage quality
2. What was done correctly
3. What was missing or late
4. Inspection risk if gaps remain
5. Recommendations for improvement

Format as a professional regulatory narrative suitable for audit documentation.
"""
        
        try:
            system_prompt = f"You are a pharmacovigilance inspector providing lifecycle stage assessments for signal governance quality evaluation."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=800,
                temperature=0.3
            ) or f"Stage {stage_name} narrative unavailable."
        except Exception as e:
            return f"Stage narrative generation error: {str(e)}"

