# src/ai/governance_engine.py

"""
AetherSignal Governance Engine
--------------------------------
Balanced-tone regulatory governance assistant for
signal management, oversight, audit readiness,
and compliance alignment (FDA, EMA, CIOMS).

This engine consolidates outputs from:
 - Trend alerts
 - Spike detection
 - Subgroup analysis
 - Risk prioritization framework
 - Label impact assessment
 - CAPA recommendations
 - DSUR / PBRER automation
 - Quantum anomaly detection (optional inputs)

Primary goals:
 - Provide governance oversight summaries
 - Produce balanced, clear next-step recommendations
 - Validate compliance with global safety expectations
 - Support inspections and audit defense
 - Generate signal files and lifecycle documentation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import datetime
import pandas as pd


@dataclass
class GovernanceFinding:
    """One governance finding or observation."""
    title: str
    description: str
    severity: str  # low | medium | high
    category: str  # process | signal | data | compliance | evidence
    recommendations: List[str] = field(default_factory=list)


@dataclass
class GovernanceAssessment:
    """
    The full governance assessment result for a dataset,
    signal, or overall portfolio.
    """
    generated_at: str
    signal_summary: List[str]
    key_findings: List[GovernanceFinding]
    recommended_next_steps: List[str]
    regulatory_alignment_notes: List[str]
    audit_risk_level: str
    overall_governance_score: float  # 0–100


class GovernanceEngine:
    """
    Main engine entrypoint. Produces governance assessments
    and oversight reports using a balanced professional tone.
    """

    def __init__(self, llm=None):
        """
        llm: optional LLM interface for deeper narrative outputs.
        If None, engine uses rule-based governance logic only.
        """
        self.llm = llm

    # ---------------------------------------------------------
    #  PART 1 — BASE TONE + GOVERNANCE SUMMARY GENERATORS
    # ---------------------------------------------------------

    def balanced_tone(self, text: str) -> str:
        """
        Normalize the output tone:
        - Professional
        - Clear and actionable
        - Evidence-driven but readable
        - Avoids overly formal regulatory language
        """
        return (
            text.replace("must", "should")
                .replace("MANDATORY", "required")
                .replace("!", ".")
        )

    def summarize_signals(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Convert signal objects (from trend alerts, disproportionality, etc.)
        into human-readable governance summaries.
        """
        summaries = []
        for s in signals:
            msg = (
                f"{s.get('drug', 'Unknown drug')} shows "
                f"{s.get('pattern', 'a notable pattern')} "
                f"with {s.get('metric', 'the measured indicator')}."
            )
            summaries.append(self.balanced_tone(msg))
        return summaries

    def compute_governance_score(self, findings: List[GovernanceFinding]) -> float:
        """
        Score: 100 = excellent governance, 0 = poor.
        Balanced formula:
         - high severity findings: heavy penalty
         - medium severity: moderate penalty
         - low severity: small penalty
        """
        score = 100.0
        for f in findings:
            if f.severity == "high":
                score -= 20
            elif f.severity == "medium":
                score -= 10
            else:
                score -= 3
        return max(0, min(100, score))

    # ---------------------------------------------------------
    #  PART 2 — GLOBAL REGULATORY ALIGNMENT CHECKS
    # ---------------------------------------------------------

    def evaluate_fda_alignment(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Evaluate detected signals against FDA expectations under:
         - 21 CFR 314.80 (postmarketing reporting)
         - 21 CFR 600.80 (biologics)
         - FDA Signal Management guidance (2021 draft)

        Outputs are balanced-tone statements describing:
         - Whether a signal merits further evaluation
         - Documentation adequacy
         - Need for additional analyses or CAPA
        """
        notes = []

        for s in signals:
            drug = s.get("drug", "Unknown Drug")
            metric = s.get("metric", "")
            pattern = s.get("pattern", "")

            # Signal strength check
            strength = s.get("strength", s.get("severity", "undetermined"))
            requires_eval = strength in ["moderate", "strong", "high", "critical"]

            if requires_eval:
                msg = (
                    f"Under FDA postmarketing expectations, the observation for {drug} "
                    f"({pattern}, based on {metric}) should undergo structured signal "
                    f"evaluation, including documentation of assessment methods and "
                    f"follow-up analyses."
                )
            else:
                msg = (
                    f"The current signal pattern for {drug} does not immediately indicate "
                    f"a regulatory-triggered evaluation, but ongoing monitoring is "
                    f"appropriate based on FDA expectations."
                )
            notes.append(self.balanced_tone(msg))

        # Global FDA reminder
        notes.append(
            "FDA frameworks emphasize timely evaluation, clear documentation, "
            "and evidence-based rationale for both signal confirmation and non-confirmation."
        )

        return notes

    def evaluate_ema_alignment(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Evaluate against EMA GVP Module IX (Signal Management):
         - Signal validation steps
         - Strength of evidence review
         - Emerging patterns
         - Prioritization based on patient impact

        Produces practical, balanced guidance.
        """
        notes = []

        for s in signals:
            drug = s.get("drug", "Unknown Drug")
            emerging = s.get("emerging", s.get("trend", {}).get("slope", 0) > 0)

            if emerging:
                msg = (
                    f"EMA GVP Module IX considers the pattern for {drug} suitable for "
                    f"early validation as an emerging signal, ensuring documentation of "
                    f"clinical relevance and temporal plausibility."
                )
            else:
                msg = (
                    f"EMA guidance indicates that the current data for {drug} does not "
                    f"require immediate signal validation but should remain under routine "
                    f"monitoring."
                )
            notes.append(self.balanced_tone(msg))

        notes.append(
            "EMA frameworks expect consistent signal documentation, "
            "traceability of decision-making steps, and periodic reassessment."
        )

        return notes

    def evaluate_cioms_alignment(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Evaluate signals against CIOMS VIII expectations:
         - Structured workflow
         - Clear rationale for follow-up actions
         - Evidence-based evaluation
        """
        notes = []

        for s in signals:
            drug = s.get("drug", "Unknown Drug")
            strength = s.get("strength", s.get("severity", "undetermined"))

            if strength in ["strong", "high", "critical"]:
                msg = (
                    f"CIOMS VIII guidance suggests that the observed signal for {drug} "
                    f"may benefit from prioritized assessment, ensuring that rationale and "
                    f"supporting evidence are clearly documented."
                )
            else:
                msg = (
                    f"CIOMS VIII guidance supports routine evaluation for the observed "
                    f"pattern involving {drug}, documenting reasoning and evidence."
                )

            notes.append(self.balanced_tone(msg))

        notes.append(
            "CIOMS emphasizes transparency, reproducibility, and clear justification "
            "for all signal assessment decisions."
        )

        return notes

    # Combined evaluator
    def assess_regulatory_alignment(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Aggregate and normalize all regulatory alignment notes
        from FDA, EMA, and CIOMS frameworks.
        """
        fda = self.evaluate_fda_alignment(signals)
        ema = self.evaluate_ema_alignment(signals)
        cioms = self.evaluate_cioms_alignment(signals)

        combined = self.balanced_tone(
            "The following notes summarize regulatory expectations across FDA, EMA, and CIOMS frameworks."
        )

        return [combined] + fda + ema + cioms

    # ---------------------------------------------------------
    #  PART 3 — SIGNAL VALIDATION LOGIC
    #  Evidence Strength, Timelines, Documentation Completeness
    # ---------------------------------------------------------

    def grade_evidence_strength(self, signal: Dict[str, Any]) -> str:
        """
        Grade evidence strength for a signal.
        
        Returns:
            "weak" | "moderate" | "strong" | "very_strong"
        """
        # Extract evidence indicators
        case_count = signal.get("case_count", signal.get("count", 0))
        rpf_score = signal.get("rpf_score", 0)
        ror = signal.get("ror", signal.get("ROR", 1))
        prr = signal.get("prr", signal.get("PRR", 1))
        seriousness_pct = signal.get("seriousness_pct", signal.get("serious_percent", 0))
        trend_strength = signal.get("trend_strength", signal.get("trend", {}).get("slope", 0))
        
        score = 0
        
        # Case count contribution
        if case_count >= 50:
            score += 3
        elif case_count >= 20:
            score += 2
        elif case_count >= 5:
            score += 1
        
        # Disproportionality contribution
        disproportionality = max(ror, prr)
        if disproportionality >= 5:
            score += 3
        elif disproportionality >= 3:
            score += 2
        elif disproportionality >= 2:
            score += 1
        
        # Seriousness contribution
        if seriousness_pct >= 50:
            score += 2
        elif seriousness_pct >= 20:
            score += 1
        
        # Trend strength contribution
        if trend_strength > 0.5:
            score += 2
        elif trend_strength > 0.2:
            score += 1
        
        # RPF score contribution
        if rpf_score >= 80:
            score += 3
        elif rpf_score >= 60:
            score += 2
        elif rpf_score >= 40:
            score += 1
        
        # Grade assignment
        if score >= 12:
            return "very_strong"
        elif score >= 8:
            return "strong"
        elif score >= 4:
            return "moderate"
        else:
            return "weak"

    def check_timeline_compliance(self, signal: Dict[str, Any]) -> Optional[GovernanceFinding]:
        """
        Check if signal meets timeline compliance expectations.
        
        FDA/EMA expect:
         - Initial assessment within 30 days for high-priority signals
         - Documentation within 60 days for routine signals
         - Follow-up actions tracked and completed
        
        Returns:
            GovernanceFinding if timeline issue detected, None otherwise
        """
        detected_date = signal.get("detected_on", signal.get("detected_date"))
        if not detected_date:
            return None
        
        try:
            if isinstance(detected_date, str):
                detected = datetime.datetime.fromisoformat(detected_date.replace('Z', '+00:00'))
            else:
                detected = detected_date
        except:
            return None
        
        days_since_detection = (datetime.datetime.now(detected.tzinfo) - detected).days if detected.tzinfo else (datetime.datetime.utcnow() - detected.replace(tzinfo=None)).days
        
        priority = signal.get("priority", signal.get("risk_level", "Medium"))
        status = signal.get("status", "New")
        
        # High/Critical priority signals should be assessed within 30 days
        if priority in ["High", "Critical"] and status not in ["Closed", "Archived"]:
            if days_since_detection > 30:
                return GovernanceFinding(
                    title=f"Timeline Compliance Issue: {signal.get('drug', 'Signal')}",
                    description=(
                        f"High-priority signal detected {days_since_detection} days ago. "
                        f"FDA/EMA expectations suggest initial assessment should be completed within 30 days. "
                        f"Current status: {status}."
                    ),
                    severity="high",
                    category="compliance",
                    recommendations=[
                        "Complete initial signal assessment within 5 business days.",
                        "Document assessment rationale and next steps.",
                        "Update signal status to 'In Review' or 'Under Assessment'."
                    ]
                )
            elif days_since_detection > 20:
                return GovernanceFinding(
                    title=f"Timeline Reminder: {signal.get('drug', 'Signal')}",
                    description=(
                        f"High-priority signal approaching 30-day assessment deadline "
                        f"({days_since_detection} days since detection)."
                    ),
                    severity="medium",
                    category="compliance",
                    recommendations=[
                        "Schedule assessment review meeting.",
                        "Prepare preliminary assessment documentation."
                    ]
                )
        
        # Routine signals should have documentation within 60 days
        elif priority in ["Medium", "Low"] and status not in ["Closed", "Archived"]:
            if days_since_detection > 60:
                return GovernanceFinding(
                    title=f"Documentation Timeline: {signal.get('drug', 'Signal')}",
                    description=(
                        f"Signal detected {days_since_detection} days ago. "
                        f"Routine signals should have documentation completed within 60 days."
                    ),
                    severity="medium",
                    category="compliance",
                    recommendations=[
                        "Complete signal documentation and assessment rationale.",
                        "Update signal status appropriately."
                    ]
                )
        
        return None

    def check_documentation_completeness(self, signal: Dict[str, Any]) -> List[GovernanceFinding]:
        """
        Check if signal has complete documentation per regulatory expectations.
        
        Required documentation:
         - Signal detection method
         - Assessment rationale
         - Evidence summary
         - Decision rationale
         - Next steps / CAPA
        
        Returns:
            List of GovernanceFindings for missing documentation
        """
        findings = []
        drug = signal.get("drug", "Unknown Drug")
        
        # Check for required fields
        missing_items = []
        
        if not signal.get("assessment_rationale") and not signal.get("ai_summary"):
            missing_items.append("Assessment rationale")
        
        if not signal.get("evidence_summary") and not signal.get("evidence"):
            missing_items.append("Evidence documentation")
        
        if not signal.get("decision_rationale") and signal.get("status") in ["Closed", "Archived"]:
            missing_items.append("Decision rationale for closure")
        
        if signal.get("priority") in ["High", "Critical"] and not signal.get("next_steps"):
            missing_items.append("Next steps / action plan")
        
        if missing_items:
            severity = "high" if signal.get("priority") in ["High", "Critical"] else "medium"
            findings.append(GovernanceFinding(
                title=f"Incomplete Documentation: {drug}",
                description=(
                    f"The signal for {drug} is missing the following documentation elements: "
                    f"{', '.join(missing_items)}. Complete documentation is required for "
                    f"regulatory compliance and audit readiness."
                ),
                severity=severity,
                category="evidence",
                recommendations=[
                    f"Complete documentation for: {item}" for item in missing_items
                ] + [
                    "Ensure all assessment decisions are documented with rationale.",
                    "Attach relevant evidence and analysis results."
                ]
            ))
        
        return findings

    def validate_signal_lifecycle(self, signal: Dict[str, Any]) -> List[GovernanceFinding]:
        """
        Validate that signal has proper lifecycle progression.
        
        Expected lifecycle:
         New → In Review → Under Assessment → (Escalated) → Closed/Archived
        
        Checks:
         - Status transitions are logical
         - Required steps are completed at each stage
         - No signals stuck in intermediate states too long
        """
        findings = []
        drug = signal.get("drug", "Unknown Drug")
        status = signal.get("status", "New")
        detected_date = signal.get("detected_on", signal.get("detected_date"))
        
        if not detected_date:
            return findings
        
        try:
            if isinstance(detected_date, str):
                detected = datetime.datetime.fromisoformat(detected_date.replace('Z', '+00:00'))
            else:
                detected = detected_date
        except:
            return findings
        
        days_since_detection = (datetime.datetime.now(detected.tzinfo) - detected).days if detected.tzinfo else (datetime.datetime.utcnow() - detected.replace(tzinfo=None)).days
        
        priority = signal.get("priority", "Medium")
        
        # Check for signals stuck in "New" status too long
        if status == "New" and days_since_detection > 14:
            findings.append(GovernanceFinding(
                title=f"Signal Lifecycle Issue: {drug}",
                description=(
                    f"Signal has remained in 'New' status for {days_since_detection} days. "
                    f"Signals should progress to 'In Review' within 7-14 days of detection."
                ),
                severity="medium" if priority != "Critical" else "high",
                category="process",
                recommendations=[
                    "Review signal and transition to 'In Review' status.",
                    "Assign owner if not already assigned.",
                    "Schedule initial assessment meeting."
                ]
            ))
        
        # Check for signals in "In Review" without owner
        if status == "In Review" and not signal.get("owner"):
            findings.append(GovernanceFinding(
                title=f"Missing Owner: {drug}",
                description=(
                    f"Signal is in 'In Review' status but has no assigned owner. "
                    f"Ownership assignment is required for accountability and tracking."
                ),
                severity="medium",
                category="process",
                recommendations=[
                    "Assign signal owner (PV Lead or QPPV).",
                    "Update signal metadata with owner information."
                ]
            ))
        
        # Check for signals in intermediate states too long
        if status in ["In Review", "Under Assessment"] and days_since_detection > 90:
            findings.append(GovernanceFinding(
                title=f"Extended Assessment Period: {drug}",
                description=(
                    f"Signal has been in '{status}' status for {days_since_detection} days. "
                    f"Extended assessment periods may indicate resource constraints or "
                    f"complexity requiring escalation."
                ),
                severity="medium" if priority != "Critical" else "high",
                category="process",
                recommendations=[
                    "Review signal complexity and resource requirements.",
                    "Consider escalation if additional expertise is needed.",
                    "Document reasons for extended assessment period."
                ]
            ))
        
        return findings

    def assess_signal_validation(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive signal validation assessment.
        
        Combines:
         - Evidence strength grading
         - Timeline compliance
         - Documentation completeness
         - Lifecycle validation
        
        Returns:
            Dictionary with validation results
        """
        evidence_strength = self.grade_evidence_strength(signal)
        timeline_issue = self.check_timeline_compliance(signal)
        doc_findings = self.check_documentation_completeness(signal)
        lifecycle_findings = self.validate_signal_lifecycle(signal)
        
        all_findings = []
        if timeline_issue:
            all_findings.append(timeline_issue)
        all_findings.extend(doc_findings)
        all_findings.extend(lifecycle_findings)
        
        # Determine validation status
        has_high_severity = any(f.severity == "high" for f in all_findings)
        validation_status = "needs_attention" if has_high_severity else ("review_needed" if all_findings else "compliant")
        
        return {
            "evidence_strength": evidence_strength,
            "validation_status": validation_status,
            "findings": all_findings,
            "timeline_compliant": timeline_issue is None,
            "documentation_complete": len(doc_findings) == 0,
            "lifecycle_valid": len(lifecycle_findings) == 0
        }

    # ---------------------------------------------------------
    #  PART 3 — SIGNAL VALIDATION ENGINE (CIOMS VIII / EMA GVP Module IX / FDA)
    #  Evidence Strength, Clinical Plausibility, Temporal Association,
    #  Dose-Response, Consistency, Case Quality, Validation Status
    # ---------------------------------------------------------

    def evaluate_signal_evidence_strength(self, signal: Dict[str, Any]) -> str:
        """
        Score the evidence strength of a detected signal based on:
        - Disproportionality magnitude
        - Temporal association strength
        - Consistency across subgroups
        - Case narrative richness
        - Biological/clinical plausibility
        - Trend change significance
        - Presence of serious outcomes
        
        Returns:
            "weak" | "moderate" | "strong"
        """
        score = 0

        # Disproportionality (PRR/ROR/EBGM surrogate)
        metric = signal.get("metric_value", signal.get("ror", signal.get("prr", 1)))
        if metric > 5:
            score += 2
        elif metric > 3:
            score += 1

        # Trend growth (slope)
        slope = signal.get("slope", signal.get("trend", {}).get("slope", 0) if isinstance(signal.get("trend"), dict) else 0)
        if slope > 0.15:
            score += 2
        elif slope > 0.05:
            score += 1

        # Serious outcomes
        if signal.get("serious", False) or signal.get("serious_count", 0) > 0:
            score += 1

        # Subgroup consistency
        subgroups = signal.get("subgroup_hits", len(signal.get("subgroups", {}).keys()) if isinstance(signal.get("subgroups"), dict) else 0)
        if subgroups >= 3:
            score += 2
        elif subgroups >= 1:
            score += 1

        # Biological plausibility
        if signal.get("plausible_mechanism", signal.get("clinical_plausibility", False)):
            score += 1

        # Narrative quality
        if signal.get("narratives_rich", signal.get("narrative_clusters") and len(signal.get("narrative_clusters", [])) > 0):
            score += 1

        # Determine category
        if score >= 6:
            return "strong"
        elif score >= 3:
            return "moderate"
        else:
            return "weak"

    def check_signal_documentation_completeness(self, signal: Dict[str, Any]) -> List[str]:
        """
        Checks whether signal documentation meets expectations for:
        - Signal description
        - Data reviewed
        - Assessment rationale
        - Impact analysis
        - Expected next steps
        
        Returns:
            List of missing documentation items or completion confirmation
        """
        missing = []

        if not signal.get("assessment_summary") and not signal.get("ai_summary"):
            missing.append("Assessment summary not documented.")

        if not signal.get("clinical_relevance") and not signal.get("llm_explanation"):
            missing.append("Clinical relevance statement missing.")

        if not signal.get("impact_analysis") and not signal.get("label_impact"):
            missing.append("Impact analysis not provided.")

        if not signal.get("next_steps") and not signal.get("suggested_action"):
            missing.append("Next-step recommendations not documented.")

        if not missing:
            return ["Documentation appears complete and aligned with expectations."]

        return missing

    def evaluate_signal_priority(self, strength: str, signal: Dict[str, Any]) -> str:
        """
        Determine priority level based on:
        - Evidence strength
        - Seriousness of outcomes
        - Trend acceleration
        - Vulnerable populations
        - Batch/lot concentration
        
        Returns:
            "low" | "medium" | "high"
        """
        priority_score = 0

        if strength == "strong":
            priority_score += 2
        elif strength == "moderate":
            priority_score += 1

        if signal.get("serious", False) or signal.get("serious_count", 0) > 0:
            priority_score += 2

        slope = signal.get("slope", signal.get("trend", {}).get("slope", 0) if isinstance(signal.get("trend"), dict) else 0)
        if slope > 0.2:
            priority_score += 1

        if signal.get("vulnerable_population", signal.get("subgroups", {}).get("age_bucket", {}).get("top_group") == "pediatric" if isinstance(signal.get("subgroups"), dict) else False):
            priority_score += 1

        if signal.get("batch_cluster", signal.get("lot_alerts") and len(signal.get("lot_alerts", [])) > 0):
            priority_score += 1

        if priority_score >= 5:
            return "high"
        elif priority_score >= 3:
            return "medium"
        else:
            return "low"

    def evaluate_signal_timelines(self, signal: Dict[str, Any]) -> str:
        """
        Determine whether the signal is within the expected
        regulatory evaluation timelines.

        EMA GVP: 30 days for validated signals.
        FDA: 'Timely evaluation'
        
        Returns:
            Timeline compliance status message
        """
        validated_date = signal.get("validated_date", signal.get("detected_on", signal.get("detected_date")))
        if not validated_date:
            return "Validation date not recorded."

        try:
            if isinstance(validated_date, str):
                validated = pd.Timestamp(validated_date)
            else:
                validated = pd.Timestamp(validated_date)
        except:
            return "Validation date format not recognized."

        now = pd.Timestamp.now()
        days = (now - validated).days

        if days <= 30:
            return "Evaluation timeline in compliance (within 30 days)."
        else:
            return f"Evaluation may exceed expected timelines ({days} days since detection)."

    def validate_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master signal validation function:
        - Evidence strength scoring
        - Documentation completeness check
        - Priority determination
        - Timeline status
        
        Returns:
            Dictionary with validation results
        """
        strength = self.evaluate_signal_evidence_strength(signal)
        documentation = self.check_signal_documentation_completeness(signal)
        priority = self.evaluate_signal_priority(strength, signal)
        timeline = self.evaluate_signal_timelines(signal)

        return {
            "drug": signal.get("drug", "Unknown"),
            "reaction": signal.get("reaction", signal.get("event", "Unknown")),
            "strength": strength,
            "priority": priority,
            "documentation_issues": documentation,
            "timeline_status": timeline,
        }

    def validate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate all detected signals in a batch.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of validation result dictionaries
        """
        results = []
        for s in signals:
            results.append(self.validate_signal(s))
        return results

    # ---------------------------------------------------------
    #  PART 4 — SIGNAL LIFECYCLE + TRACEABILITY + AI RATIONALE
    # ---------------------------------------------------------

    def classify_signal_lifecycle(self, signal: Dict[str, Any]) -> str:
        """
        Classify the lifecycle state of a signal using:
        - Evidence strength
        - Trend/Prioritization
        - Regulatory timeline
        - Emerging signal flags
        - Case quality indicators
        
        Returns:
            Lifecycle state string
        """
        strength = signal.get("strength", signal.get("evidence_strength", "weak"))
        priority = signal.get("priority", signal.get("risk_level", "low"))
        emerging = signal.get("emerging", False)
        validated = signal.get("validated_date") or signal.get("detected_on")
        confirmed = signal.get("confirmed", False)
        closed = signal.get("closed", signal.get("status") in ["Closed", "Archived"])

        # 7. Closed / Not Confirmed
        if closed:
            return "Closed / Not Confirmed"

        # 6. Confirmed Risk
        if confirmed:
            return "Confirmed Risk"

        # 5. Potential Risk
        if strength == "strong" and priority == "high":
            return "Potential Risk"

        # 4. Under Assessment
        if validated and priority in ["medium", "high"]:
            return "Under Assessment"

        # 3. Validated
        if validated and strength in ["moderate", "strong"]:
            return "Validated Signal"

        # 1. Emerging
        if emerging and strength in ["weak", "moderate"]:
            return "Emerging Signal"

        # 2. New / Initial
        if strength == "weak" and not validated:
            return "Initial Observation"

        return "Initial Observation"

    def build_ai_rationale(self, signal: Dict[str, Any]) -> str:
        """
        Generate a balanced-tone rationale for why the signal
        was categorized, prioritized, validated, or closed.
        
        Returns:
            Balanced-tone rationale text
        """
        drug = signal.get("drug", "the drug")
        reaction = signal.get("reaction", signal.get("event", "the reaction"))
        strength = signal.get("strength", signal.get("evidence_strength", "undetermined"))
        priority = signal.get("priority", signal.get("risk_level", "undetermined"))
        lifecycle = signal.get("lifecycle", self.classify_signal_lifecycle(signal))

        rationale = (
            f"The current assessment for {drug}–{reaction} indicates "
            f"{self.balanced_tone('that evidence strength is assessed as ' + strength)}. "
            f"Priority has been assigned as {priority}, and the lifecycle classification "
            f"is {lifecycle}. This reflects the available case data, observed trends, "
            f"and consistency of findings across subgroups."
        )

        if strength == "strong":
            rationale += (
                " A higher evidence strength is influenced by significant disproportionality, "
                "consistent patterns across subgroups, and plausible biological mechanisms."
            )

        if lifecycle == "Emerging Signal":
            rationale += (
                " As an emerging signal, routine validation steps are recommended to determine "
                "clinical relevance and regulatory impact."
            )

        if lifecycle == "Validated Signal":
            rationale += (
                " With the signal validated, structured evaluation and documentation are expected "
                "to continue, including assessment of clinical impact and benefit–risk implications."
            )

        if lifecycle == "Potential Risk":
            rationale += (
                " Given the potential risk classification, further investigation and escalation "
                "through governance channels may be appropriate."
            )

        return self.balanced_tone(rationale)

    def build_traceability_entry(self, signal: Dict[str, Any], user: str = "System") -> Dict[str, Any]:
        """
        Create an inspection-ready trace entry.
        Similar to Argus, Veeva Vault Safety, Empirica Topics.
        
        Returns:
            Trace entry dictionary
        """
        lifecycle = signal.get("lifecycle", self.classify_signal_lifecycle(signal))
        now = datetime.datetime.utcnow()

        return {
            "timestamp": now.isoformat(),
            "user": user,
            "drug": signal.get("drug", "Unknown"),
            "reaction": signal.get("reaction", signal.get("event", "Unknown")),
            "lifecycle": lifecycle,
            "strength": signal.get("strength", signal.get("evidence_strength", "undetermined")),
            "priority": signal.get("priority", signal.get("risk_level", "undetermined")),
            "timeline_status": signal.get("timeline_status", "Not assessed"),
            "documentation_issues": signal.get("documentation_issues", []),
            "rationale": signal.get("rationale", self.build_ai_rationale(signal)),
        }

    def enrich_signals_with_governance(self, validated_signals: List[Dict[str, Any]], user: str = "System") -> List[Dict[str, Any]]:
        """
        Full governance pipeline for each signal:
        - Lifecycle classification
        - AI-based rationale generation
        - Traceability entry creation
        
        Args:
            validated_signals: List of validated signal dictionaries
            user: User identifier for traceability
            
        Returns:
            List of enriched signal dictionaries
        """
        enriched = []
        for s in validated_signals:
            lifecycle = self.classify_signal_lifecycle(s)
            s["lifecycle"] = lifecycle
            s["rationale"] = self.build_ai_rationale(s)
            s["trace_log"] = self.build_traceability_entry(s, user)
            enriched.append(s)
        return enriched

    # ---------------------------------------------------------
    #  PART 5 — CHECKLIST, GAP DETECTION & REVIEWER GUIDANCE
    # ---------------------------------------------------------

    def generate_governance_checklist(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate checklist items based on global signal management standards:
        - EMA GVP Module IX
        - CIOMS VIII
        - FDA Postmarketing Guidance
        - MHRA Safety Review expectations
        
        Returns:
            List of checklist items with completion status
        """
        checklist = [
            {
                "item": "Signal validated with appropriate evidence",
                "completed": bool(signal.get("validated_date") or signal.get("detected_on"))
            },
            {
                "item": "Trend analysis completed",
                "completed": bool(signal.get("trend_analysis_done", signal.get("trend") or signal.get("time_series")))
            },
            {
                "item": "Subgroup analysis performed",
                "completed": bool(signal.get("subgroup_analysis_done", signal.get("subgroups")))
            },
            {
                "item": "Case quality review completed",
                "completed": bool(signal.get("case_quality_review", False))
            },
            {
                "item": "Clinical relevance assessed",
                "completed": bool(signal.get("clinical_assessment_done", signal.get("clinical_relevance") or signal.get("llm_explanation")))
            },
            {
                "item": "Benefit–risk impact evaluated",
                "completed": bool(signal.get("br_completed", signal.get("benefit_risk")))
            },
            {
                "item": "Label impact assessment completed",
                "completed": bool(signal.get("label_impact_done", signal.get("label_impact")))
            },
            {
                "item": "Governance review documented",
                "completed": bool(signal.get("governance_reviewed", signal.get("trace_log")))
            },
            {
                "item": "Timeline compliance met",
                "completed": bool("timeline" in str(signal.get("timeline_status", "")).lower() and "compliance" in str(signal.get("timeline_status", "")).lower() or signal.get("timeline_compliant", False))
            },
            {
                "item": "Disproportionality analysis completed",
                "completed": bool(signal.get("ror") or signal.get("prr") or signal.get("disproportionality_analysis"))
            },
            {
                "item": "Risk prioritization (RPF) completed",
                "completed": bool(signal.get("rpf_score") or signal.get("risk_level"))
            },
            {
                "item": "Documentation complete and rationale provided",
                "completed": bool(signal.get("rationale") or signal.get("ai_summary") or signal.get("assessment_summary"))
            }
        ]

        return checklist

    def detect_documentation_gaps(self, checklist: List[Dict[str, Any]]) -> List[str]:
        """
        Identify missing or incomplete compliance items.
        
        Args:
            checklist: List of checklist items
            
        Returns:
            List of missing item descriptions
        """
        return [
            item["item"]
            for item in checklist
            if not item["completed"]
        ]

    def compute_governance_compliance_score(self, checklist: List[Dict[str, Any]]) -> float:
        """
        Compute a 0–100 compliance and readiness score.
        
        Args:
            checklist: List of checklist items
            
        Returns:
            Compliance score (0-100)
        """
        if not checklist:
            return 0.0
        
        total = len(checklist)
        completed = sum(1 for item in checklist if item["completed"])
        return round((completed / total) * 100, 2)

    def generate_reviewer_guidance(self, signal: Dict[str, Any], gaps: List[str]) -> str:
        """
        Provide AI guidance to reviewers on next steps.
        Balanced tone, designed for audit defense.
        
        Args:
            signal: Signal dictionary
            gaps: List of missing documentation items
            
        Returns:
            Guidance text
        """
        if not gaps:
            return (
                "All core governance steps appear to be addressed. "
                "It may be appropriate to prepare a summary for governance review, "
                "including benefit–risk implications and any required CAPA follow-up."
            )

        guidance = [
            "The following governance elements require attention:"
        ]

        for g in gaps:
            guidance.append(f"• {g}")

        guidance.append(
            self.balanced_tone(
                "Completion of these items will strengthen the assessment and ensure "
                "regulatory and internal governance expectations are met."
            )
        )

        # Add priority-specific guidance
        priority = signal.get("priority", signal.get("risk_level", "low"))
        if priority in ["High", "high", "Critical", "critical"]:
            guidance.append(
                "Given the high priority classification, expedited completion of missing "
                "elements is recommended to ensure timely signal assessment."
            )

        return "\n".join(guidance)

    def enrich_with_governance_compliance(self, signal: Dict[str, Any], user: str = "System") -> Dict[str, Any]:
        """
        Full Part 5 pipeline:
        - Generate checklist
        - Detect gaps
        - Compute readiness score
        - Provide reviewer guidance
        
        Args:
            signal: Signal dictionary
            user: User identifier for traceability
            
        Returns:
            Enriched signal dictionary
        """
        checklist = self.generate_governance_checklist(signal)
        gaps = self.detect_documentation_gaps(checklist)
        score = self.compute_governance_compliance_score(checklist)
        guidance = self.generate_reviewer_guidance(signal, gaps)

        signal["governance_checklist"] = checklist
        signal["governance_gaps"] = gaps
        signal["governance_score"] = score
        signal["reviewer_guidance"] = guidance

        return signal

    # ---------------------------------------------------------
    #  PART 6 — TIMELINE COMPLIANCE + DUE-DATE CALCULATOR
    # ---------------------------------------------------------

    def calculate_due_dates(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create regulatory-aligned due dates based on:
        - Signal priority
        - Evidence strength
        - Lifecycle state
        
        Based on:
        - EMA GVP Module IX timelines
        - CIOMS VIII best practices
        - FDA "timely evaluation" expectations
        
        Returns:
            Dictionary with validation_due, assessment_due, finalization_due
        """
        priority = signal.get("priority", signal.get("risk_level", "low"))
        validated_date = signal.get("validated_date") or signal.get("detected_on") or signal.get("detected_date")
        
        if not validated_date:
            return {
                "validation_due": None,
                "assessment_due": None,
                "finalization_due": None
            }

        try:
            validated_date = pd.to_datetime(validated_date)
        except:
            # If parsing fails, use current date as fallback
            validated_date = pd.Timestamp.now()

        # Timelines based on typical governance standards
        if priority in ["High", "high", "Critical", "critical"]:
            validation_days = 7
            assessment_days = 30
            final_days = 60
        elif priority in ["Medium", "medium"]:
            validation_days = 14
            assessment_days = 45
            final_days = 75
        else:
            validation_days = 21
            assessment_days = 60
            final_days = 90

        return {
            "validation_due": (validated_date + pd.Timedelta(days=validation_days)).isoformat(),
            "assessment_due": (validated_date + pd.Timedelta(days=assessment_days)).isoformat(),
            "finalization_due": (validated_date + pd.Timedelta(days=final_days)).isoformat(),
        }

    def detect_timeline_deviation(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect late/missed regulatory timelines and classify severity.
        
        Returns:
            Dictionary with validation_status, assessment_status, finalization_status
        """
        due_dates = signal.get("due_dates", {})
        now = pd.Timestamp.now()

        def check_due(due_date_str):
            if not due_date_str:
                return "Not Applicable"
            
            try:
                due_date = pd.to_datetime(due_date_str)
            except:
                return "Not Applicable"
            
            if now <= due_date:
                return "On Time"
            
            days_overdue = (now - due_date).days
            
            if days_overdue <= 14:
                return "Slight Delay"
            elif days_overdue <= 30:
                return "Moderate Delay"
            else:
                return "Severe Delay"

        return {
            "validation_status": check_due(due_dates.get("validation_due")),
            "assessment_status": check_due(due_dates.get("assessment_due")),
            "finalization_status": check_due(due_dates.get("finalization_due")),
        }

    def generate_timeline_guidance(self, signal: Dict[str, Any]) -> str:
        """
        Provide AI reasoning and guidance about timeline performance.
        
        Returns:
            Guidance text
        """
        statuses = signal.get("timeline_status", {})
        priority = signal.get("priority", signal.get("risk_level", "low"))

        # Check if all statuses are "On Time" or "Not Applicable"
        relevant_statuses = {k: v for k, v in statuses.items() if v != "Not Applicable"}
        
        if not relevant_statuses:
            return "Timeline status not yet applicable for this signal."
        
        if all(v == "On Time" for v in relevant_statuses.values()):
            return (
                f"All timeline expectations for this {priority}-priority signal "
                f"have been met so far. Continued monitoring is recommended."
            )

        guidance = ["Timeline deviations detected:"]

        for step, status in statuses.items():
            if status != "On Time" and status != "Not Applicable":
                step_name = step.replace("_", " ").replace("status", "").title().strip()
                guidance.append(f"• {step_name}: {status}")

        guidance.append(
            self.balanced_tone(
                "Addressing these delays will support compliance with internal governance "
                "and regulatory expectations. Escalation may be appropriate if delays persist."
            )
        )

        return "\n".join(guidance)

    def enrich_with_timeline_compliance(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all Part 6 components:
        - Due date calculator
        - Deviation detector
        - AI timeline guidance
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Enriched signal dictionary
        """
        due_dates = self.calculate_due_dates(signal)
        
        # Create a temporary signal dict with due_dates for deviation detection
        temp_signal = signal.copy()
        temp_signal["due_dates"] = due_dates
        
        status = self.detect_timeline_deviation(temp_signal)
        guidance = self.generate_timeline_guidance({
            "timeline_status": status,
            "priority": signal.get("priority", signal.get("risk_level", "low"))
        })

        signal["due_dates"] = due_dates
        signal["timeline_status"] = status
        signal["timeline_guidance"] = guidance

        return signal

    # ---------------------------------------------------------
    #  PART 7 — OVERSIGHT METRICS, HEATMAPS & WORKLOAD FORECASTING
    # ---------------------------------------------------------

    def compute_oversight_metrics(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute global governance KPIs for dashboards:
        - Lifecycle distribution
        - Timeline performance
        - Risk class distribution
        - Reviewer workload
        - Backlog and escalation needs
        
        Returns:
            Dictionary with oversight metrics
        """
        if not signals:
            return {
                "lifecycle_distribution": {},
                "timeline_overview": {},
                "priority_distribution": {},
                "governance_score_stats": {},
                "total_signals": 0
            }

        df = pd.DataFrame(signals)

        metrics = {"total_signals": len(signals)}

        # --- Lifecycle distribution ---
        if "lifecycle" in df.columns:
            metrics["lifecycle_distribution"] = df["lifecycle"].value_counts().to_dict()
        else:
            metrics["lifecycle_distribution"] = {}

        # --- Timeline status ---
        timeline_overview = {
            "on_time": 0,
            "slight_delay": 0,
            "moderate_delay": 0,
            "severe_delay": 0,
            "not_applicable": 0
        }
        
        for s in signals:
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "Not Applicable")
                if assessment_status == "On Time":
                    timeline_overview["on_time"] += 1
                elif assessment_status == "Slight Delay":
                    timeline_overview["slight_delay"] += 1
                elif assessment_status == "Moderate Delay":
                    timeline_overview["moderate_delay"] += 1
                elif assessment_status == "Severe Delay":
                    timeline_overview["severe_delay"] += 1
                else:
                    timeline_overview["not_applicable"] += 1
        
        metrics["timeline_overview"] = timeline_overview

        # --- Priority distribution ---
        if "priority" in df.columns:
            metrics["priority_distribution"] = df["priority"].value_counts().to_dict()
        elif "risk_level" in df.columns:
            metrics["priority_distribution"] = df["risk_level"].value_counts().to_dict()
        else:
            metrics["priority_distribution"] = {}

        # --- Governance Scores ---
        if "governance_score" in df.columns:
            scores = df["governance_score"].dropna()
            if len(scores) > 0:
                metrics["governance_score_stats"] = {
                    "avg": float(scores.mean()),
                    "min": float(scores.min()),
                    "max": float(scores.max()),
                    "median": float(scores.median())
                }
            else:
                metrics["governance_score_stats"] = {}
        else:
            metrics["governance_score_stats"] = {}

        # --- Overdue signals count ---
        overdue_count = sum(1 for s in signals if s.get("timeline_status", {}).get("assessment_status") in ["Moderate Delay", "Severe Delay"])
        metrics["overdue_signals"] = overdue_count

        # --- High priority count ---
        high_priority_count = sum(1 for s in signals if s.get("priority") in ["High", "high", "Critical", "critical"] or s.get("risk_level") in ["High", "high", "Critical", "critical"])
        metrics["high_priority_count"] = high_priority_count

        return metrics

    def generate_heatmap_matrix(self, signals: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Heatmap matrix for:
        - Priority vs Compliance
        - Lifecycle vs Timeline Status
        
        Returns:
            DataFrame suitable for heatmap visualization
        """
        if not signals:
            return pd.DataFrame()

        rows = []
        for s in signals:
            priority = s.get("priority", s.get("risk_level", "unknown"))
            lifecycle = s.get("lifecycle", "unknown")
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                timeline = timeline_status.get("assessment_status", "unknown")
            else:
                timeline = "unknown"
            governance_score = s.get("governance_score", 0)

            rows.append({
                "priority": str(priority),
                "lifecycle": str(lifecycle),
                "timeline_status": str(timeline),
                "governance_score": float(governance_score) if governance_score else 0.0
            })

        df = pd.DataFrame(rows)
        return df

    def forecast_governance_workload(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict governance workload for next 30, 60, 90 days:
        - Based on due dates
        - Severity
        - Aging signals
        - Priority load
        
        Returns:
            Dictionary with workload forecast
        """
        now = pd.Timestamp.now()
        horizon_30 = now + pd.Timedelta(days=30)
        horizon_60 = now + pd.Timedelta(days=60)
        horizon_90 = now + pd.Timedelta(days=90)

        forecast = {
            "due_30_days": 0,
            "due_60_days": 0,
            "due_90_days": 0,
            "aging_signals": 0,
            "high_priority_load": 0,
            "moderate_priority_load": 0,
            "low_priority_load": 0
        }

        for s in signals:
            due_dates = s.get("due_dates", {})
            assessment_due = due_dates.get("assessment_due")
            
            if assessment_due:
                try:
                    assessment_due_dt = pd.to_datetime(assessment_due)
                    
                    if assessment_due_dt <= horizon_30:
                        forecast["due_30_days"] += 1
                    if assessment_due_dt <= horizon_60:
                        forecast["due_60_days"] += 1
                    if assessment_due_dt <= horizon_90:
                        forecast["due_90_days"] += 1
                except:
                    pass

            # Aging signal (validated more than 90 days ago)
            validated_date = s.get("validated_date") or s.get("detected_on") or s.get("detected_date")
            if validated_date:
                try:
                    validated_dt = pd.to_datetime(validated_date)
                    if (now - validated_dt) > pd.Timedelta(days=90):
                        forecast["aging_signals"] += 1
                except:
                    pass

            # Priority workload distribution
            priority = s.get("priority", s.get("risk_level", "low"))
            if priority in ["High", "high", "Critical", "critical"]:
                forecast["high_priority_load"] += 1
            elif priority in ["Medium", "medium"]:
                forecast["moderate_priority_load"] += 1
            else:
                forecast["low_priority_load"] += 1

        return forecast

    def compute_governance_burden_index(self, signals: List[Dict[str, Any]], team_capacity: int = 10) -> float:
        """
        A single composite score:
        (backlog × priority × overdue weight) / team capacity
        
        Returns:
            Burden index (higher = more burdened)
        """
        if not signals:
            return 0.0

        backlog = len(signals)
        
        # Priority weights
        priority_weights = {
            "Critical": 4.0,
            "critical": 4.0,
            "High": 3.0,
            "high": 3.0,
            "Medium": 2.0,
            "medium": 2.0,
            "Low": 1.0,
            "low": 1.0
        }
        
        # Calculate weighted priority sum
        weighted_priority = 0
        for s in signals:
            priority = s.get("priority", s.get("risk_level", "low"))
            weight = priority_weights.get(priority, 1.0)
            
            # Overdue weight multiplier
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "")
                if assessment_status == "Severe Delay":
                    weight *= 2.0
                elif assessment_status == "Moderate Delay":
                    weight *= 1.5
                elif assessment_status == "Slight Delay":
                    weight *= 1.2
            
            weighted_priority += weight
        
        # Burden index
        burden_index = (backlog * (weighted_priority / backlog) * 1.0) / max(team_capacity, 1)
        
        return round(burden_index, 2)

    # ---------------------------------------------------------
    #  PART 8 — GOVERNANCE MEETING AUTOMATION + PRE-READ BUILDER
    # ---------------------------------------------------------

    def _extract_top_risks(self, signals: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Extract top risk signals based on governance score.
        
        Args:
            signals: List of signal dictionaries
            limit: Number of top risks to return
            
        Returns:
            List of top risk signals
        """
        sorted_signals = sorted(
            signals,
            key=lambda x: x.get("governance_score", 0),
            reverse=True
        )
        return sorted_signals[:limit]

    def _get_delayed_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract signals with moderate or severe timeline delays.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of delayed signals
        """
        delayed = []
        for s in signals:
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "")
                if assessment_status in ["Moderate Delay", "Severe Delay"]:
                    delayed.append(s)
        return delayed

    def _get_high_priority_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract high or critical priority signals.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of high-priority signals
        """
        high_priority = []
        for s in signals:
            priority = s.get("priority", s.get("risk_level", "low"))
            if priority in ["High", "high", "Critical", "critical"]:
                high_priority.append(s)
        return high_priority

    def _get_aging_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract signals validated more than 90 days ago.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of aging signals
        """
        now = pd.Timestamp.now()
        aging = []
        
        for s in signals:
            validated_date = s.get("validated_date") or s.get("detected_on") or s.get("detected_date")
            if validated_date:
                try:
                    validated_dt = pd.to_datetime(validated_date)
                    if (now - validated_dt) > pd.Timedelta(days=90):
                        aging.append(s)
                except:
                    pass
        
        return aging

    def _generate_recommended_governance_actions(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        Determines governance-level actions needed based on signal portfolio.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of recommended action strings
        """
        actions = []

        # Severe timeline delays
        severe = [
            s for s in signals
            if isinstance(s.get("timeline_status", {}), dict) and
            s.get("timeline_status", {}).get("assessment_status") == "Severe Delay"
        ]
        if severe:
            actions.append(
                f"{len(severe)} signal(s) require immediate escalation due to severe timeline delay."
            )

        # High priority with backlog
        high_priority = self._get_high_priority_signals(signals)
        if high_priority:
            actions.append(
                f"{len(high_priority)} high-priority signal(s) require urgent assessment resourcing."
            )

        # Aging signals
        aging = self._get_aging_signals(signals)
        if aging:
            actions.append(
                f"{len(aging)} signal(s) are aging (>90 days) and may need governance decisions."
            )

        # Governance score threshold
        threshold = [
            s for s in signals
            if s.get("governance_score", 0) < 50
        ]
        if threshold:
            actions.append(
                f"{len(threshold)} signal(s) have governance scores below 50 and may need "
                f"documentation or process improvement."
            )

        # Overdue assessments
        overdue = [
            s for s in signals
            if isinstance(s.get("timeline_status", {}), dict) and
            s.get("timeline_status", {}).get("assessment_status") in ["Moderate Delay", "Severe Delay"]
        ]
        if overdue:
            actions.append(
                f"{len(overdue)} signal(s) have overdue assessments and require timeline compliance review."
            )

        return actions if actions else ["No immediate governance actions required."]

    def build_governance_preread(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a fully structured Governance Pre-Read pack.
        This is returned as a dictionary ready for UI or PDF export.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            Complete governance pre-read pack dictionary
        """
        metrics = self.compute_oversight_metrics(signals)
        heatmap = self.generate_heatmap_matrix(signals)
        forecast = self.forecast_governance_workload(signals)
        burden_index = self.compute_governance_burden_index(signals)

        pack = {
            "title": "Signal Governance Pre-Read",
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "summary": {
                "total_signals": len(signals),
                "lifecycle": metrics.get("lifecycle_distribution", {}),
                "priority": metrics.get("priority_distribution", {}),
                "timeline": metrics.get("timeline_overview", {}),
                "governance_score": metrics.get("governance_score_stats", {}),
                "burden_index": burden_index,
                "overdue_signals": metrics.get("overdue_signals", 0),
                "high_priority_count": metrics.get("high_priority_count", 0),
            },
            "heatmap_matrix": heatmap.to_dict(orient="records") if not heatmap.empty else [],
            "workload_forecast": forecast,
            "top_risks": [
                {
                    "drug": s.get("drug", "Unknown"),
                    "reaction": s.get("reaction", s.get("event", "Unknown")),
                    "governance_score": s.get("governance_score", 0),
                    "priority": s.get("priority", s.get("risk_level", "low")),
                    "lifecycle": s.get("lifecycle", "Unknown")
                }
                for s in self._extract_top_risks(signals, limit=10)
            ],
            "delayed_signals": [
                {
                    "drug": s.get("drug", "Unknown"),
                    "reaction": s.get("reaction", s.get("event", "Unknown")),
                    "timeline_status": s.get("timeline_status", {}),
                    "priority": s.get("priority", s.get("risk_level", "low"))
                }
                for s in self._get_delayed_signals(signals)
            ],
            "high_priority": [
                {
                    "drug": s.get("drug", "Unknown"),
                    "reaction": s.get("reaction", s.get("event", "Unknown")),
                    "priority": s.get("priority", s.get("risk_level", "low")),
                    "governance_score": s.get("governance_score", 0)
                }
                for s in self._get_high_priority_signals(signals)
            ],
            "aging": [
                {
                    "drug": s.get("drug", "Unknown"),
                    "reaction": s.get("reaction", s.get("event", "Unknown")),
                    "validated_date": s.get("validated_date") or s.get("detected_on"),
                    "days_old": (
                        (pd.Timestamp.now() - pd.to_datetime(s.get("validated_date") or s.get("detected_on")))
                        .days if s.get("validated_date") or s.get("detected_on") else None
                    )
                }
                for s in self._get_aging_signals(signals)
            ],
            "recommended_actions": self._generate_recommended_governance_actions(signals)
        }

        return pack

    def build_quarterly_governance_pack(self, signals: List[Dict[str, Any]], quarter: str = None) -> Dict[str, Any]:
        """
        Builds a quarterly governance pack with aggregated metrics.
        
        Args:
            signals: List of signal dictionaries
            quarter: Quarter identifier (e.g., "Q1 2024")
            
        Returns:
            Quarterly governance pack dictionary
        """
        if not quarter:
            now = datetime.datetime.now()
            quarter = f"Q{(now.month - 1) // 3 + 1} {now.year}"

        preread = self.build_governance_preread(signals)
        
        # Add quarterly-specific sections
        preread["title"] = f"Quarterly Signal Governance Pack - {quarter}"
        preread["quarter"] = quarter
        preread["quarterly_summary"] = {
            "signals_closed": len([s for s in signals if s.get("lifecycle") == "Closed / Not Confirmed"]),
            "signals_validated": len([s for s in signals if s.get("lifecycle") == "Validated Signal"]),
            "signals_under_assessment": len([s for s in signals if s.get("lifecycle") == "Under Assessment"]),
            "average_assessment_time": self._compute_average_assessment_time(signals),
            "compliance_rate": self._compute_compliance_rate(signals)
        }

        return preread

    def _compute_average_assessment_time(self, signals: List[Dict[str, Any]]) -> Optional[float]:
        """Compute average time from validation to closure in days."""
        times = []
        for s in signals:
            validated = s.get("validated_date") or s.get("detected_on")
            closed = s.get("closed_date") or (s.get("status") == "Closed" and s.get("updated_at"))
            
            if validated and closed:
                try:
                    days = (pd.to_datetime(closed) - pd.to_datetime(validated)).days
                    if days > 0:
                        times.append(days)
                except:
                    pass
        
        return round(sum(times) / len(times), 1) if times else None

    def _compute_compliance_rate(self, signals: List[Dict[str, Any]]) -> float:
        """Compute percentage of signals meeting timeline compliance."""
        if not signals:
            return 0.0
        
        on_time = sum(
            1 for s in signals
            if isinstance(s.get("timeline_status", {}), dict) and
            s.get("timeline_status", {}).get("assessment_status") == "On Time"
        )
        
        return round((on_time / len(signals)) * 100, 2)

    # ---------------------------------------------------------
    #  PART 9 — REVIEWER ASSIGNMENT ENGINE
    # ---------------------------------------------------------

    def load_reviewer_profiles(self) -> List[Dict[str, Any]]:
        """
        Placeholder: in the future this will load reviewer metadata 
        from Supabase. For now, static or user-provided config.
        
        Returns:
            List of reviewer profile dictionaries
        """
        return [
            {
                "name": "Dr. A",
                "expertise": ["Biologics", "Dermatology", "Immunology"],
                "max_workload": 5,
                "current_workload": 2,
                "regions": ["US", "EU"],
            },
            {
                "name": "Dr. B",
                "expertise": ["Cardiology", "Small Molecules"],
                "max_workload": 6,
                "current_workload": 4,
                "regions": ["US"],
            },
            {
                "name": "Dr. C",
                "expertise": ["CNS", "Psychiatry"],
                "max_workload": 4,
                "current_workload": 1,
                "regions": ["EU", "APAC"],
            },
            {
                "name": "Dr. D",
                "expertise": ["Oncology", "Hematology"],
                "max_workload": 5,
                "current_workload": 0,
                "regions": ["US", "EU", "APAC"],
            }
        ]

    def assign_reviewers_to_signals(self, signals: List[Dict[str, Any]], reviewer_profiles: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Assign reviewers to signals based on expertise, workload, priority,
        governance score, and region alignment.
        
        Args:
            signals: List of signal dictionaries
            reviewer_profiles: Optional custom reviewer profiles
            
        Returns:
            List of signals with assignment information added
        """
        reviewers = reviewer_profiles or self.load_reviewer_profiles()
        results = []

        for signal in signals:
            assigned = self._assign_single_signal(signal, reviewers)
            signal["reviewer_assignment"] = assigned
            results.append(signal)

        return results

    def _assign_single_signal(self, signal: Dict[str, Any], reviewers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Logic to assign the optimal reviewer for one signal.
        
        Args:
            signal: Signal dictionary
            reviewers: List of reviewer profile dictionaries
            
        Returns:
            Assignment dictionary with reviewer and reasoning
        """
        drug = signal.get("drug", "").lower()
        reaction = signal.get("reaction", signal.get("event", "")).lower()
        region = signal.get("region", "US")
        priority = signal.get("priority", signal.get("risk_level", "medium")).lower()
        governance_score = signal.get("governance_score", 0)

        # Phase 1: Filter by region
        region_matches = [r for r in reviewers if region in r.get("regions", [])]

        # If no region-specific reviewer exists → fallback to all
        candidates = region_matches if region_matches else reviewers

        # Phase 2: Filter by expertise (drug class or SOC)
        expertise_matches = []
        for r in candidates:
            expertise_str = " ".join(r.get("expertise", [])).lower()
            if any(
                kw in expertise_str
                for kw in [drug, reaction]
                if kw
            ):
                expertise_matches.append(r)

        if expertise_matches:
            candidates = expertise_matches

        # Phase 3: Workload scoring
        def workload_score(r):
            capacity = r.get("max_workload", 5) - r.get("current_workload", 0)
            return max(capacity, 0)

        # Phase 4: Priority and governance score weighting
        def reviewer_priority_score(r):
            base_score = workload_score(r)
            priority_bonus = 5 if priority in ["high", "critical"] else 0
            governance_bonus = governance_score / 20
            return base_score + priority_bonus + governance_bonus

        if not candidates:
            return {
                "assigned_to": "Unassigned",
                "reason": ["No suitable reviewer available."],
                "workload_status": "unknown"
            }

        best = max(candidates, key=reviewer_priority_score)

        # Update workload (in-memory only - in production, persist to database)
        best["current_workload"] = best.get("current_workload", 0) + 1

        return {
            "assigned_to": best.get("name", "Unknown"),
            "reason": self._build_assignment_reason(best, signal),
            "workload_status": "available" if workload_score(best) > 0 else "near_capacity",
            "reviewer_expertise": best.get("expertise", []),
            "reviewer_regions": best.get("regions", [])
        }

    def _build_assignment_reason(self, reviewer: Dict[str, Any], signal: Dict[str, Any]) -> List[str]:
        """
        Build transparent assignment reasoning for governance auditability.
        
        Args:
            reviewer: Reviewer profile dictionary
            signal: Signal dictionary
            
        Returns:
            List of reason strings
        """
        reasons = []

        priority = signal.get("priority", signal.get("risk_level", "medium"))
        if priority in ["High", "high", "Critical", "critical"]:
            reasons.append("High-priority signal requires experienced reviewer.")

        governance_score = signal.get("governance_score", 0)
        if governance_score >= 80:
            reasons.append("Elevated governance score indicates increased risk.")

        drug = signal.get("drug", "").lower()
        reaction = signal.get("reaction", signal.get("event", "")).lower()
        expertise_str = " ".join(reviewer.get("expertise", [])).lower()
        
        if drug and drug in expertise_str:
            reasons.append(f"Reviewer has expertise in {drug} or related drug class.")
        elif reaction and any(r_term in expertise_str for r_term in reaction.split()):
            reasons.append(f"Reviewer has expertise in {reaction} or related therapeutic area.")

        current_workload = reviewer.get("current_workload", 0)
        max_workload = reviewer.get("max_workload", 5)
        if current_workload < max_workload:
            capacity = max_workload - current_workload
            reasons.append(f"Reviewer has available workload capacity ({capacity} slots remaining).")

        region = signal.get("region", "US")
        if region in reviewer.get("regions", []):
            reasons.append(f"Reviewer covers region {region}.")

        if not reasons:
            reasons.append("Assignment based on general availability and workload balance.")

        return reasons

    def compute_reviewer_workload_distribution(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute workload distribution across reviewers.
        
        Args:
            signals: List of signals with reviewer assignments
            
        Returns:
            Dictionary with workload distribution metrics
        """
        assignments = {}
        
        for s in signals:
            assignment = s.get("reviewer_assignment", {})
            reviewer = assignment.get("assigned_to", "Unassigned")
            
            if reviewer not in assignments:
                assignments[reviewer] = {
                    "count": 0,
                    "high_priority": 0,
                    "delayed": 0
                }
            
            assignments[reviewer]["count"] += 1
            
            priority = s.get("priority", s.get("risk_level", "low"))
            if priority in ["High", "high", "Critical", "critical"]:
                assignments[reviewer]["high_priority"] += 1
            
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "")
                if assessment_status in ["Moderate Delay", "Severe Delay"]:
                    assignments[reviewer]["delayed"] += 1
        
        return assignments

    # ---------------------------------------------------------
    #  PART 10 — REVIEWER WORKLOAD FORECASTING
    # ---------------------------------------------------------

    def forecast_reviewer_workload(self, signals: List[Dict[str, Any]], horizon_days: int = 30, reviewer_profiles: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Forecast reviewer workload using upcoming deadlines, risk scores,
        and reviewer capacity. Returns a detailed workload forecast object.
        
        Args:
            signals: List of signal dictionaries
            horizon_days: Forecast horizon in days (default 30)
            reviewer_profiles: Optional custom reviewer profiles
            
        Returns:
            Dictionary with forecast details
        """
        reviewers = reviewer_profiles or self.load_reviewer_profiles()
        
        # Assign signals to reviewers
        assignments = self.assign_reviewers_to_signals(signals, reviewers)
        
        # Build a mapping: reviewer → list of assigned signals
        reviewer_map = {}
        for sig in assignments:
            assignment = sig.get("reviewer_assignment", {})
            reviewer_name = assignment.get("assigned_to", "Unassigned")
            signal_id = sig.get("signal_id", sig.get("drug", "Unknown"))
            reviewer_map.setdefault(reviewer_name, []).append(signal_id)
        
        forecast = []
        
        for r in reviewers:
            name = r["name"]
            current = r.get("current_workload", 0)
            max_cap = r.get("max_workload", 5)
            
            assigned_signal_ids = reviewer_map.get(name, [])
            
            # Predict growth: high-risk signals tend to produce more work
            growth_factor = self._predict_growth_factor(assigned_signal_ids, signals, reviewer_map.get(name, []))
            
            # Forecast workload within horizon
            projected = int(current + growth_factor)
            
            forecast.append({
                "reviewer": name,
                "current_workload": current,
                "max_capacity": max_cap,
                "assigned_signals_count": len(assigned_signal_ids),
                "assigned_signals": assigned_signal_ids[:5],  # Limit to first 5 for display
                "growth_factor": round(growth_factor, 1),
                "projected_workload": projected,
                "over_capacity": projected > max_cap,
                "capacity_utilization_pct": round((projected / max_cap * 100) if max_cap > 0 else 0, 1),
                "risk_level": self._classify_capacity_risk(projected, max_cap),
            })
        
        return {
            "horizon_days": horizon_days,
            "forecast": forecast,
            "summary": self._aggregate_forecast_summary(forecast)
        }

    def _predict_growth_factor(self, assigned_signal_ids: List[str], all_signals: List[Dict[str, Any]], assigned_signals: List[str]) -> float:
        """
        Predicts workload increase based on high-risk signals.
        
        Args:
            assigned_signal_ids: List of signal IDs assigned to reviewer
            all_signals: All available signals
            assigned_signals: List of signal identifiers (backup)
            
        Returns:
            Predicted growth factor (additional workload units)
        """
        if not assigned_signal_ids and not assigned_signals:
            return 0.0
        
        # Extract signals relevant to this reviewer
        # Try to match by signal_id first, then by drug name
        subset = []
        for s in all_signals:
            signal_id = s.get("signal_id") or s.get("drug", "")
            if signal_id in assigned_signal_ids or signal_id in assigned_signals:
                subset.append(s)
            elif s.get("drug", "") in assigned_signal_ids or s.get("drug", "") in assigned_signals:
                subset.append(s)
        
        growth = 0.0
        
        for s in subset:
            score = s.get("governance_score", 0)
            priority = s.get("priority", s.get("risk_level", "medium")).lower()
            
            # High governance score → more future workload
            if score >= 80:
                growth += 1.5
            elif score >= 60:
                growth += 1.0
            elif score >= 40:
                growth += 0.5
            
            # Priority-based workload multiplier
            if priority in ["high", "critical"]:
                growth += 2.0
            elif priority == "medium":
                growth += 1.0
            else:
                growth += 0.5
            
            # Timeline delays increase workload
            timeline_status = s.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "")
                if assessment_status == "Severe Delay":
                    growth += 1.0
                elif assessment_status == "Moderate Delay":
                    growth += 0.5
        
        return growth

    def _classify_capacity_risk(self, projected: int, max_cap: int) -> str:
        """
        Classify capacity risk based on projected vs max capacity.
        
        Args:
            projected: Projected workload
            max_cap: Maximum capacity
            
        Returns:
            Risk level string
        """
        if max_cap == 0:
            return "unknown"
        
        pct = projected / max_cap
        
        if pct >= 1.2:
            return "critical"
        elif pct >= 1.0:
            return "high"
        elif pct >= 0.75:
            return "medium"
        else:
            return "low"

    def _aggregate_forecast_summary(self, forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate forecast summary statistics.
        
        Args:
            forecast: List of reviewer forecast dictionaries
            
        Returns:
            Summary dictionary
        """
        total = len(forecast)
        
        risk_counts = {
            "critical": sum(1 for f in forecast if f.get("risk_level") == "critical"),
            "high": sum(1 for f in forecast if f.get("risk_level") == "high"),
            "medium": sum(1 for f in forecast if f.get("risk_level") == "medium"),
            "low": sum(1 for f in forecast if f.get("risk_level") == "low"),
        }
        
        total_projections = sum(f.get("projected_workload", 0) for f in forecast)
        total_capacity = sum(f.get("max_capacity", 0) for f in forecast)
        overall_utilization = round((total_projections / total_capacity * 100) if total_capacity > 0 else 0, 1)
        
        return {
            "total_reviewers": total,
            "risk_distribution": risk_counts,
            "at_risk_reviewers": risk_counts["critical"] + risk_counts["high"],
            "over_capacity_reviewers": sum(1 for f in forecast if f.get("over_capacity", False)),
            "total_projected_workload": total_projections,
            "total_capacity": total_capacity,
            "overall_utilization_pct": overall_utilization
        }

    # ---------------------------------------------------------
    #  PART 11 — COMPLIANCE CHECKLIST ENGINE
    # ---------------------------------------------------------

    def load_compliance_rules(self) -> List[Dict[str, Any]]:
        """
        Regulatory-aligned compliance rules (ICH, GVP, FDA).
        This can be externalized later into a YAML or database.
        
        Returns:
            List of compliance rule dictionaries
        """
        return [
            {
                "id": "E2C_R2_01",
                "text": "Signal validated.",
                "category": "Signal Validation",
                "critical": True,
                "regulation": "ICH E2C(R2)"
            },
            {
                "id": "GVP_IX_030",
                "text": "Causal association evaluated.",
                "category": "Causality Assessment",
                "critical": True,
                "regulation": "EMA GVP Module IX"
            },
            {
                "id": "FDA_SM_12",
                "text": "Frequency and severity trends analyzed.",
                "category": "Trend Analysis",
                "critical": True,
                "regulation": "FDA Signal Management"
            },
            {
                "id": "GVP_IX_070",
                "text": "Aggregate data sources assessed.",
                "category": "Evidence Package",
                "critical": True,
                "regulation": "EMA GVP Module IX"
            },
            {
                "id": "GVP_IX_090",
                "text": "Rationale for prioritization documented.",
                "category": "Governance Rationale",
                "critical": False,
                "regulation": "EMA GVP Module IX"
            },
            {
                "id": "ICH_E2C_45",
                "text": "Risk minimization considerations included.",
                "category": "Risk Minimization",
                "critical": False,
                "regulation": "ICH E2C(R2)"
            },
            {
                "id": "INSPECT_03",
                "text": "Signal follow-up plan drafted.",
                "category": "Follow-Up Actions",
                "critical": True,
                "regulation": "FDA Inspection Guidance"
            },
            {
                "id": "GVP_IX_120",
                "text": "Subgroup analysis completed (age, sex, region).",
                "category": "Subgroup Analysis",
                "critical": False,
                "regulation": "EMA GVP Module IX"
            },
            {
                "id": "FDA_DOC_05",
                "text": "Case narratives reviewed for quality.",
                "category": "Case Quality",
                "critical": False,
                "regulation": "FDA Documentation Standards"
            },
            {
                "id": "GVP_IX_150",
                "text": "Benefit-risk assessment performed.",
                "category": "Benefit-Risk",
                "critical": False,
                "regulation": "EMA GVP Module IX"
            },
            {
                "id": "LABEL_IMPACT_01",
                "text": "Label impact assessment completed.",
                "category": "Label Impact",
                "critical": False,
                "regulation": "FDA/EMA Labeling Requirements"
            },
            {
                "id": "TIMELINE_01",
                "text": "Regulatory timelines met or documented deviation.",
                "category": "Timeline Compliance",
                "critical": True,
                "regulation": "EMA/FDA Timeline Expectations"
            }
        ]

    def evaluate_compliance_for_signal(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Automatically evaluates compliance status for a single signal.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            List of compliance check results
        """
        rules = self.load_compliance_rules()
        
        results = []
        
        for r in rules:
            rule_id = r["id"]
            completed = False
            
            # Rule mappings (expandable later with NLP/document parsing)
            if rule_id == "E2C_R2_01":
                completed = bool(
                    signal.get("validated_date") or
                    signal.get("validated", False) or
                    signal.get("lifecycle") in ["Validated Signal", "Under Assessment", "Potential Risk", "Confirmed Risk"]
                )
            
            elif rule_id == "GVP_IX_030":
                completed = bool(
                    signal.get("causality_assessed", False) or
                    signal.get("clinical_relevance") or
                    signal.get("llm_explanation")
                )
            
            elif rule_id == "FDA_SM_12":
                completed = bool(
                    signal.get("trend_analysis_complete", False) or
                    signal.get("trend") or
                    signal.get("time_series") or
                    signal.get("trend_analysis_done", False)
                )
            
            elif rule_id == "GVP_IX_070":
                completed = bool(
                    signal.get("evidence_package_complete", False) or
                    signal.get("evidence_summary") or
                    signal.get("subgroups") or
                    signal.get("rpf_score") is not None
                )
            
            elif rule_id == "GVP_IX_090":
                completed = bool(
                    signal.get("priority_rationale") or
                    signal.get("rationale") or
                    signal.get("reviewer_guidance")
                )
            
            elif rule_id == "ICH_E2C_45":
                completed = bool(
                    signal.get("risk_minimization_considered", False) or
                    signal.get("capa_recommendations") or
                    signal.get("risk_minimization")
                )
            
            elif rule_id == "INSPECT_03":
                completed = bool(
                    signal.get("follow_up_plan") or
                    signal.get("next_steps") or
                    signal.get("recommended_actions")
                )
            
            elif rule_id == "GVP_IX_120":
                completed = bool(
                    signal.get("subgroup_analysis_done", False) or
                    signal.get("subgroups") or
                    signal.get("subgroup_analysis")
                )
            
            elif rule_id == "FDA_DOC_05":
                completed = bool(
                    signal.get("case_quality_review", False) or
                    signal.get("case_narratives_reviewed", False)
                )
            
            elif rule_id == "GVP_IX_150":
                completed = bool(
                    signal.get("br_completed", False) or
                    signal.get("benefit_risk") or
                    signal.get("benefit_risk_assessment")
                )
            
            elif rule_id == "LABEL_IMPACT_01":
                completed = bool(
                    signal.get("label_impact_done", False) or
                    signal.get("label_impact") or
                    signal.get("label_assessment")
                )
            
            elif rule_id == "TIMELINE_01":
                timeline_status = signal.get("timeline_status", {})
                if isinstance(timeline_status, dict):
                    assessment_status = timeline_status.get("assessment_status", "")
                    # On Time or documented deviation (any status means it was tracked)
                    completed = assessment_status != "" or signal.get("timeline_guidance")
                else:
                    completed = False
            
            results.append({
                "id": r["id"],
                "text": r["text"],
                "category": r["category"],
                "regulation": r["regulation"],
                "critical": r["critical"],
                "completed": completed,
                "missing": not completed
            })
        
        return results

    def compute_compliance_score(self, checklist: List[Dict[str, Any]]) -> float:
        """
        Computes compliance score (0–100) weighted by criticality.
        
        Args:
            checklist: List of compliance check results
            
        Returns:
            Compliance score (0-100)
        """
        if not checklist:
            return 0.0
        
        total = len(checklist)
        critical_items = [c for c in checklist if c.get("critical", False)]
        total_critical = len(critical_items)
        
        if total_critical == 0:
            # No critical items, use simple percentage
            completed = sum(1 for c in checklist if c.get("completed", False))
            return round((completed / total) * 100, 1)
        
        completed = sum(1 for c in checklist if c.get("completed", False))
        completed_critical = sum(1 for c in critical_items if c.get("completed", False))
        
        # Weighted score: 40% general completion, 60% critical completion
        score = (
            (completed / total) * 0.4 +
            (completed_critical / total_critical) * 0.6
        ) * 100
        
        return round(score, 1)

    def explain_compliance_gaps(self, checklist: List[Dict[str, Any]]) -> List[str]:
        """
        Returns a human-readable explanation of missing compliance items.
        
        Args:
            checklist: List of compliance check results
            
        Returns:
            List of gap explanation strings
        """
        missing = [c for c in checklist if c.get("missing", False)]
        
        if not missing:
            return ["All compliance items completed."]
        
        explanations = []
        
        # Separate critical and non-critical
        critical_missing = [c for c in missing if c.get("critical", False)]
        non_critical_missing = [c for c in missing if not c.get("critical", False)]
        
        if critical_missing:
            explanations.append("⚠️ CRITICAL COMPLIANCE GAPS (High Risk):")
            for m in critical_missing:
                explanations.append(f"  ❗ {m['text']} ({m['regulation']})")
        
        if non_critical_missing:
            explanations.append("\n⚠️ NON-CRITICAL GAPS (Medium Risk):")
            for m in non_critical_missing:
                explanations.append(f"  • {m['text']} ({m['regulation']})")
        
        return explanations

    def generate_compliance_report(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive compliance report for all signals.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            Complete compliance report dictionary
        """
        report = {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "total_signals": len(signals),
            "signals": []
        }
        
        overall_scores = []
        
        for signal in signals:
            checklist = self.evaluate_compliance_for_signal(signal)
            score = self.compute_compliance_score(checklist)
            gaps = self.explain_compliance_gaps(checklist)
            
            signal_report = {
                "drug": signal.get("drug", "Unknown"),
                "reaction": signal.get("reaction", signal.get("event", "Unknown")),
                "compliance_score": score,
                "checklist": checklist,
                "gaps": gaps,
                "critical_gaps_count": sum(1 for c in checklist if c.get("missing", False) and c.get("critical", False)),
                "total_gaps_count": sum(1 for c in checklist if c.get("missing", False))
            }
            
            report["signals"].append(signal_report)
            overall_scores.append(score)
        
        # Aggregate statistics
        if overall_scores:
            report["summary"] = {
                "average_compliance_score": round(sum(overall_scores) / len(overall_scores), 1),
                "min_compliance_score": round(min(overall_scores), 1),
                "max_compliance_score": round(max(overall_scores), 1),
                "signals_below_threshold": sum(1 for s in overall_scores if s < 70),
                "signals_fully_compliant": sum(1 for s in overall_scores if s == 100)
            }
        
        return report
