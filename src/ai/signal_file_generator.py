"""
Signal File Generator (CHUNK 6.21.1 - Part 12)
Generates complete regulatory-ready signal files with evidence packages,
trend analysis, compliance checklists, risk assessments, and governance notes.
"""
import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

from .governance_engine import GovernanceEngine
from .risk_prioritization import RiskPrioritizationEngine
from .trend_alerts import detect_trend_alerts, TrendAlert


class SignalFileGenerator:
    """
    Generates a complete signal file for a given signal_id.
    Includes evidence package, trends, compliance, governance, etc.
    """

    def __init__(self, dataset: Dict[str, Any]):
        """
        Initialize the Signal File Generator.
        
        Args:
            dataset: Dictionary containing signals and data
        """
        self.dataset = dataset
        self.governance = GovernanceEngine()
        self.risk = RiskPrioritizationEngine()

    def load_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Finds a signal from dataset or memory store.
        
        Args:
            signal_id: Signal identifier (can be drug-reaction pair or unique ID)
            
        Returns:
            Signal dictionary or None if not found
        """
        # Check in signals list
        signals = self.dataset.get("signals", [])
        if isinstance(signals, list):
            for s in signals:
                if s.get("signal_id") == signal_id or s.get("id") == signal_id:
                    return s
                # Also match by drug-reaction pair
                if s.get("drug") and s.get("reaction"):
                    if f"{s.get('drug')} - {s.get('reaction')}" == signal_id:
                        return s
        
        # Check if signal_id is in dataset directly
        if signal_id in self.dataset:
            return self.dataset[signal_id]
        
        return None

    def build_evidence_package(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build core evidence package for the signal.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Evidence package dictionary
        """
        return {
            "description": signal.get("description", signal.get("summary", "")),
            "drug": signal.get("drug", "Unknown"),
            "reaction": signal.get("reaction", signal.get("event", "Unknown")),
            "cases": signal.get("cases", signal.get("count", 0)),
            "serious_cases": signal.get("serious_cases", signal.get("serious_count", 0)),
            "fatal_cases": signal.get("fatal_cases", signal.get("fatal_count", 0)),
            "time_window": signal.get("time_window", signal.get("detected_on", "")),
            "data_sources": signal.get("data_sources", ["FAERS"]),
            "detected_on": signal.get("detected_on", signal.get("detected_date", "")),
            "validated_on": signal.get("validated_date", ""),
            "lifecycle": signal.get("lifecycle", "Initial Observation")
        }

    def build_trend_analysis(self, signal: Dict[str, Any], df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Build trend analysis using heavy mode trend alerts.
        
        Args:
            signal: Signal dictionary
            df: Optional DataFrame for trend analysis
            
        Returns:
            Trend analysis dictionary
        """
        if df is None:
            df = self.dataset.get("data", pd.DataFrame())
        
        if df.empty:
            return {
                "alerts": [],
                "summary": "No data available for trend analysis."
            }
        
        # Filter DataFrame for this signal
        drug = signal.get("drug", "")
        reaction = signal.get("reaction", signal.get("event", ""))
        
        if drug and "drug" in df.columns:
            filtered_df = df[df["drug"].astype(str).str.contains(str(drug), case=False, na=False)]
            if reaction and "reaction" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["reaction"].astype(str).str.contains(str(reaction), case=False, na=False)]
        else:
            filtered_df = df
        
        # Run heavy trend analysis
        try:
            trend_result = detect_trend_alerts(filtered_df, mode="heavy")
            
            alerts = []
            if isinstance(trend_result, dict):
                alerts_list = trend_result.get("alerts", [])
                if alerts_list:
                    for alert in alerts_list:
                        if isinstance(alert, TrendAlert):
                            alerts.append({
                                "title": alert.title,
                                "severity": alert.severity,
                                "summary": alert.summary,
                                "metric_value": alert.metric_value,
                                "metric_unit": alert.metric_unit,
                                "suggested_action": alert.suggested_action
                            })
                        elif isinstance(alert, dict):
                            alerts.append(alert)
            else:
                alerts = []
            
            return {
                "alerts": alerts,
                "summary": f"Found {len(alerts)} trend alert(s) for {drug} - {reaction}",
                "mode": "heavy"
            }
        except Exception as e:
            return {
                "alerts": [],
                "summary": f"Trend analysis error: {str(e)}"
            }

    def build_compliance(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build compliance checklist for the signal.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Compliance dictionary with checklist, score, and gaps
        """
        checklist = self.governance.evaluate_compliance_for_signal(signal)
        score = self.governance.compute_compliance_score(checklist)
        gaps = self.governance.explain_compliance_gaps(checklist)
        
        return {
            "checklist": checklist,
            "score": score,
            "gaps": gaps,
            "critical_gaps": [g for g in checklist if g.get("missing", False) and g.get("critical", False)]
        }

    def build_risk_assessment(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build risk profile using RPF engine.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Risk assessment dictionary
        """
        try:
            risk_result = self.risk.score_signal(signal)
            return {
                "rpf_score": risk_result.get("rpf_score", 0),
                "risk_level": risk_result.get("risk_level", "Low"),
                "sub_scores": risk_result.get("scores", {}),
                "weights": self.risk.weights
            }
        except Exception as e:
            return {
                "rpf_score": 0,
                "risk_level": "Low",
                "error": str(e)
            }

    def build_reviewer_assignment(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build reviewer assignment information.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Reviewer assignment dictionary
        """
        # Use governance engine to assign reviewer
        try:
            assignments = self.governance.assign_reviewers_to_signals([signal])
            if assignments and len(assignments) > 0:
                assignment = assignments[0].get("reviewer_assignment", {})
                return {
                    "reviewer": assignment.get("assigned_to", "Unassigned"),
                    "reason": assignment.get("reason", []),
                    "workload_status": assignment.get("workload_status", "unknown")
                }
        except Exception as e:
            pass
        
        # Fallback to signal's existing assignment
        return {
            "reviewer": signal.get("assigned_to", signal.get("reviewer", "Unassigned")),
            "reason": signal.get("assignment_reason", ["No assignment reason provided"]),
            "workload_status": "unknown"
        }

    def build_followup_plan(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build follow-up action plan.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Follow-up plan dictionary
        """
        # Extract from signal's existing fields
        next_steps = signal.get("next_steps", signal.get("recommended_actions", []))
        if isinstance(next_steps, str):
            next_steps = [next_steps]
        
        # Use reviewer guidance from governance if available
        guidance = signal.get("reviewer_guidance", "")
        if guidance and isinstance(guidance, str):
            next_steps.append(guidance)
        
        # Add compliance gap remediation steps
        compliance = self.build_compliance(signal)
        if compliance.get("critical_gaps"):
            next_steps.append("Address critical compliance gaps identified in checklist")
        
        return {
            "steps": next_steps if next_steps else ["Monitor signal and reassess in 30 days"],
            "priority": signal.get("priority", signal.get("risk_level", "Medium")),
            "timeline": signal.get("timeline_guidance", "Follow standard signal assessment timeline")
        }

    def generate_ai_summary(self, signal: Dict[str, Any], evidence: Dict[str, Any], 
                           trends: Dict[str, Any], risk: Dict[str, Any], 
                           compliance: Dict[str, Any]) -> str:
        """
        Generate AI summary in regulatory-style PV writing.
        
        Args:
            signal: Signal dictionary
            evidence: Evidence package
            trends: Trend analysis
            risk: Risk assessment
            compliance: Compliance checklist
            
        Returns:
            AI-generated summary text
        """
        drug = evidence.get("drug", "the drug")
        reaction = evidence.get("reaction", "the reaction")
        cases = evidence.get("cases", 0)
        rpf_score = risk.get("rpf_score", 0)
        risk_level = risk.get("risk_level", "Low")
        compliance_score = compliance.get("score", 0)
        
        summary_parts = [
            f"This signal file summarizes the safety signal for {drug} and {reaction}.",
            f"The signal was detected based on {cases} case(s) and has been assigned a Risk Prioritization Framework (RPF) score of {rpf_score:.1f}, corresponding to a {risk_level} risk level."
        ]
        
        # Add trend information
        trend_alerts = trends.get("alerts", [])
        if trend_alerts:
            summary_parts.append(f"Trend analysis identified {len(trend_alerts)} significant alert(s), indicating emerging patterns that warrant continued monitoring.")
        
        # Add compliance status
        if compliance_score >= 80:
            summary_parts.append("Compliance checklist indicates strong regulatory alignment with GVP Module IX, FDA Signal Management, and ICH E2C(R2) requirements.")
        elif compliance_score >= 60:
            summary_parts.append("Compliance checklist shows adequate alignment with regulatory requirements, with some areas requiring attention.")
        else:
            summary_parts.append("Compliance checklist indicates several gaps that require remediation to meet regulatory expectations.")
        
        # Add lifecycle status
        lifecycle = evidence.get("lifecycle", "Initial Observation")
        summary_parts.append(f"The signal is currently in the '{lifecycle}' lifecycle stage, and appropriate governance processes are in place.")
        
        return " ".join(summary_parts)

    def generate_signal_file(self, signal_id: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generate complete signal file for a signal.
        
        Args:
            signal_id: Signal identifier
            df: Optional DataFrame for analysis
            
        Returns:
            Complete signal file dictionary
        """
        signal = self.load_signal(signal_id)
        
        if not signal:
            return {"error": f"Signal not found: {signal_id}"}
        
        # Build all components
        evidence = self.build_evidence_package(signal)
        trends = self.build_trend_analysis(signal, df)
        compliance = self.build_compliance(signal)
        risk = self.build_risk_assessment(signal)
        reviewer = self.build_reviewer_assignment(signal)
        followup = self.build_followup_plan(signal)
        
        # Generate AI summary
        ai_summary = self.generate_ai_summary(signal, evidence, trends, risk, compliance)
        
        return {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "signal_id": signal_id,
            "overview": signal,
            "evidence_package": evidence,
            "trends": trends,
            "compliance": compliance,
            "risk_profile": risk,
            "reviewer_assignment": reviewer,
            "followup_plan": followup,
            "ai_summary": ai_summary,
        }

