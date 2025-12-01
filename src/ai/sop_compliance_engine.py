"""
SOP Compliance Automation & Gap Scoring Engine (CHUNK 6.21.1 - Part 17)
Evaluates signal governance compliance against company SOPs, GVP Module IX, and regulatory requirements.
"""
import datetime
from typing import Dict, List, Any, Optional

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class SOPComplianceEngine:
    """
    Evaluates signal governance compliance against company SOPs,
    GVP Module IX, and internal quality rules.
    
    Produces:
    - Gap score
    - SOP deviation list
    - Timing deviations
    - Missing documentation
    - AI compliance narrative
    """

    def __init__(self, sop_text_dict: Optional[Dict[str, str]] = None):
        """
        Initialize the SOP Compliance Engine.
        
        Args:
            sop_text_dict: Dictionary mapping SOP names to their text content
                Example: {"SOP-SIG-001": "...", "SOP-SIG-002": "..."}
        """
        self.sop_text_dict = sop_text_dict or {}
        
        # Default timing rules (can be customized)
        self.timing_rules = {
            "triage_max_days": 30,
            "assessment_max_days": 60,
            "reviewer_sla_days": 5
        }

    def evaluate_compliance(self, governance_text: str, audit_trail: Dict[str, Any],
                           trend_alerts: Optional[Any] = None,
                           rpf_output: Optional[Any] = None,
                           br_output: Optional[Any] = None,
                           label_output: Optional[Any] = None,
                           capa_output: Optional[Any] = None) -> Dict[str, Any]:
        """
        Main evaluator. Returns a dictionary of compliance insights.
        
        Args:
            governance_text: Current governance package text
            audit_trail: Audit trail with timestamps and reviewer logs
            trend_alerts: Trend alerts output
            rpf_output: Risk Prioritization Framework output
            br_output: Benefit-Risk assessment output
            label_output: Label impact assessment output
            capa_output: CAPA recommendations output
            
        Returns:
            Dictionary with compliance findings and gap score
        """
        sop_findings = self._evaluate_sops(governance_text)
        timing_findings = self._evaluate_timing(audit_trail)
        missing_items = self._detect_missing_artifacts(
            governance_text, trend_alerts, rpf_output,
            br_output, label_output, capa_output
        )
        
        gap_score = self._calculate_gap_score(
            sop_findings, timing_findings, missing_items
        )
        
        ai_summary = self._generate_ai_summary(
            governance_text, sop_findings, timing_findings, missing_items, gap_score
        )
        
        return {
            "gap_score": gap_score,
            "sop_findings": sop_findings,
            "timing_findings": timing_findings,
            "missing_items": missing_items,
            "summary": ai_summary,
            "evaluated_at": datetime.datetime.utcnow().isoformat()
        }

    def _evaluate_sops(self, governance_text: str) -> Dict[str, Any]:
        """
        Compare governance text to SOP text using LLM.
        
        Args:
            governance_text: Governance package text
            
        Returns:
            Dictionary of SOP evaluation findings
        """
        findings = {}
        
        if not self.sop_text_dict:
            return {"note": "No SOPs provided for evaluation"}
        
        if not LLM_AVAILABLE:
            # Fallback: basic text matching
            for sop_name, sop_text in self.sop_text_dict.items():
                findings[sop_name] = {
                    "status": "evaluation_unavailable",
                    "note": "LLM not available for SOP comparison"
                }
            return findings
        
        for sop_name, sop_text in self.sop_text_dict.items():
            try:
                prompt = f"""
You are a GVP Module IX PV inspector.

Compare the following SOP to the governance package.

SOP ({sop_name}):
{sop_text[:2000]}

Governance Package:
{governance_text[:2000]}

List:
1. Requirements met
2. Requirements missing
3. Deviations observed
4. Potential risks of non-compliance

Format as a structured assessment suitable for audit documentation.
"""
                system_prompt = "You are a GVP Module IX PV inspector evaluating SOP compliance for signal governance."
                findings[sop_name] = call_medical_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    task_type="general",
                    max_tokens=1500,
                    temperature=0.3
                ) or "SOP evaluation unavailable."
            except Exception as e:
                findings[sop_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return findings

    def _evaluate_timing(self, audit_trail: Dict[str, Any]) -> List[str]:
        """
        Detect late triage, late assessment, overdue reviews.
        
        Args:
            audit_trail: Dictionary with timestamps and reviewer logs
                Format:
                {
                    "triage_date": datetime or ISO string,
                    "assessment_date": datetime or ISO string,
                    "finalization_date": datetime or ISO string,
                    "reviewer_logs": [
                        {"reviewer": "X", "date": datetime, "status": "complete"},
                        ...
                    ]
                }
        
        Returns:
            List of timing deviation findings
        """
        timing = []
        
        # Helper to parse dates
        def parse_date(date_value):
            if date_value is None:
                return None
            if isinstance(date_value, str):
                try:
                    return datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except:
                    return None
            return date_value
        
        # Check triage to assessment timing
        triage_date = parse_date(audit_trail.get("triage_date"))
        assessment_date = parse_date(audit_trail.get("assessment_date"))
        
        if triage_date and assessment_date:
            days_diff = (assessment_date - triage_date).days
            max_days = self.timing_rules.get("triage_max_days", 30)
            if days_diff > max_days:
                timing.append(
                    f"Signal triage exceeded {max_days}-day requirement. "
                    f"Actual: {days_diff} days."
                )
        elif not triage_date or not assessment_date:
            timing.append("Missing triage or assessment dates in audit trail.")
        
        # Check assessment to finalization timing
        finalization_date = parse_date(audit_trail.get("finalization_date"))
        if assessment_date and finalization_date:
            days_diff = (finalization_date - assessment_date).days
            max_days = self.timing_rules.get("assessment_max_days", 60)
            if days_diff > max_days:
                timing.append(
                    f"Signal assessment exceeded {max_days}-day requirement. "
                    f"Actual: {days_diff} days."
                )
        
        # Check reviewer SLA compliance
        reviewer_logs = audit_trail.get("reviewer_logs", [])
        sla_days = self.timing_rules.get("reviewer_sla_days", 5)
        
        for entry in reviewer_logs:
            reviewer = entry.get("reviewer", "Unknown")
            review_date = parse_date(entry.get("date"))
            status = entry.get("status", "")
            
            if review_date and status != "complete":
                # Check if overdue
                now = datetime.datetime.utcnow()
                if isinstance(review_date, datetime.datetime):
                    if review_date.tzinfo is None:
                        review_date = review_date.replace(tzinfo=datetime.timezone.utc)
                    days_overdue = (now.replace(tzinfo=datetime.timezone.utc) - review_date).days
                    if days_overdue > sla_days:
                        timing.append(
                            f"Reviewer {reviewer} overdue by {days_overdue - sla_days} days "
                            f"(SLA: {sla_days} days)."
                        )
        
        return timing

    def _detect_missing_artifacts(self, governance_text: str,
                                  trend_alerts: Optional[Any],
                                  rpf_output: Optional[Any],
                                  br_output: Optional[Any],
                                  label_output: Optional[Any],
                                  capa_output: Optional[Any]) -> List[str]:
        """
        Detect missing required artifacts.
        
        Args:
            governance_text: Governance package text
            trend_alerts: Trend alerts output
            rpf_output: RPF output
            br_output: Benefit-risk output
            label_output: Label impact output
            capa_output: CAPA output
            
        Returns:
            List of missing artifact descriptions
        """
        missing = []
        
        # Check for trend alerts
        if not trend_alerts:
            missing.append("Trend Alerts section is missing.")
        elif isinstance(trend_alerts, dict) and not trend_alerts.get("alerts"):
            missing.append("Trend Alerts section exists but contains no alerts.")
        
        # Check for RPF
        if not rpf_output:
            missing.append("Risk Prioritization Framework (RPF) missing.")
        
        # Check for benefit-risk assessment
        if not br_output:
            missing.append("Benefit-Risk Assessment missing.")
        
        # Check for label impact
        if not label_output:
            missing.append("Label Impact Assessment missing.")
        
        # Check for CAPA
        if not capa_output:
            missing.append("CAPA recommendations missing.")
        
        # Check for signal rationale in text
        governance_lower = governance_text.lower() if governance_text else ""
        rationale_keywords = ["signal rationale", "rationale", "justification", "reasoning"]
        if not any(keyword in governance_lower for keyword in rationale_keywords):
            missing.append("Signal rationale or justification missing in governance text.")
        
        return missing

    def _calculate_gap_score(self, sop_findings: Dict[str, Any],
                            timing_findings: List[str],
                            missing_items: List[str]) -> float:
        """
        Produces a 0–100 compliance score.
        
        Args:
            sop_findings: SOP evaluation findings
            timing_findings: List of timing deviations
            missing_items: List of missing artifacts
            
        Returns:
            Gap score (0-100, higher is better)
        """
        score = 100.0
        
        # Deduct points for timing deviations (10 points each)
        score -= len(timing_findings) * 10.0
        
        # Deduct points for missing items (10 points each)
        score -= len(missing_items) * 10.0
        
        # Deduct points for SOP findings (5 points each)
        # Only count SOPs that have errors or issues
        sop_issues = 0
        for sop_name, finding in sop_findings.items():
            if isinstance(finding, dict):
                if finding.get("status") in ["error", "non_compliant"]:
                    sop_issues += 1
            elif isinstance(finding, str) and ("missing" in finding.lower() or "deviation" in finding.lower()):
                sop_issues += 1
        
        score -= sop_issues * 5.0
        
        # Ensure score is in valid range
        return max(0.0, min(score, 100.0))

    def _generate_ai_summary(self, governance_text: str,
                            sop_findings: Dict[str, Any],
                            timing_findings: List[str],
                            missing_items: List[str],
                            gap_score: float) -> str:
        """
        Generate AI-powered compliance summary.
        
        Args:
            governance_text: Governance package text
            sop_findings: SOP evaluation findings
            timing_findings: Timing deviations
            missing_items: Missing artifacts
            gap_score: Calculated gap score
            
        Returns:
            AI-generated compliance summary
        """
        if not LLM_AVAILABLE:
            # Fallback summary
            summary_parts = [
                f"Compliance Gap Score: {gap_score:.1f}/100",
                "",
                "Findings:",
                f"  • Timing Deviations: {len(timing_findings)}",
                f"  • Missing Artifacts: {len(missing_items)}",
                f"  • SOP Findings: {len(sop_findings)}"
            ]
            if missing_items:
                summary_parts.append("\nMissing Items:")
                for item in missing_items:
                    summary_parts.append(f"  - {item}")
            if timing_findings:
                summary_parts.append("\nTiming Issues:")
                for finding in timing_findings:
                    summary_parts.append(f"  - {finding}")
            
            return "\n".join(summary_parts)
        
        try:
            prompt = f"""
You are a GVP Module IX pharmacovigilance quality inspector.

Based on the following findings, generate a compliance summary:

Gap Score: {gap_score:.1f}/100

SOP Findings:
{str(sop_findings)[:1000]}

Timing Deviations:
{chr(10).join(timing_findings) if timing_findings else "None"}

Missing Artifacts:
{chr(10).join(missing_items) if missing_items else "None"}

Governance Package (excerpt):
{governance_text[:1000]}

Provide:
1. Executive summary
2. Critical risks (if any)
3. Moderate risks (if any)
4. Minor risks (if any)
5. Recommended CAPA actions
6. Whether this would pass inspection
7. Overall assessment

Format this as a professional regulatory compliance assessment suitable for QA review and inspection documentation.
"""
            system_prompt = "You are a GVP Module IX pharmacovigilance quality inspector providing compliance assessments for regulatory audits."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=2000,
                temperature=0.3
            ) or "AI summary generation unavailable."
        except Exception as e:
            return f"AI summary generation error: {str(e)}"

