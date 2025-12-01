"""
Signal Timeline Engine (CHUNK 6.22.6)
Builds comprehensive regulatory timelines for signals with case history, trends, RPF, governance events, and regulatory actions.
Used for timeline-based inspector challenges.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.trend_alerts import detect_trend_alerts_light
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False

try:
    from src.ai.governance_engine import GovernanceEngine
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False


def build_signal_timeline(
    signal: Dict[str, Any],
    df: Optional[Any] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    rpf_history: Optional[List[Dict[str, Any]]] = None,
    governance_events: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build comprehensive signal timeline for regulatory inspection.
    
    Combines:
    - First case date
    - Case spikes and trend alerts
    - Subgroup findings over time
    - RPF score history
    - Regulatory actions
    - Governance review events
    
    Args:
        signal: Signal dictionary with drug, reaction, case data
        df: Safety data DataFrame (optional, for extracting dates)
        trend_alerts: List of trend alerts (optional)
        rpf_history: Historical RPF scores (optional)
        governance_events: Governance timeline events (optional)
        
    Returns:
        Complete timeline dictionary ready for inspection
    """
    timeline = {
        "signal_id": signal.get("id", signal.get("signal_id", "unknown")),
        "drug": signal.get("drug", signal.get("drug_name", "Unknown")),
        "reaction": signal.get("reaction", signal.get("reaction_pt", signal.get("event", "Unknown"))),
        "first_case_date": None,
        "detection_date": signal.get("detection_date", signal.get("detected_on", None)),
        "case_spikes": [],
        "trend_alerts": [],
        "subgroups": [],
        "rpf_scores": [],
        "regulatory_actions": [],
        "governance_review": [],
        "escalation_history": [],
        "label_impact_events": [],
        "timeline_summary": ""
    }
    
    # Extract first case date from DataFrame or signal data
    if df is not None and not df.empty:
        date_cols = ["event_date", "event_dt", "report_date", "received_date", "date"]
        date_col = next((col for col in date_cols if col in df.columns), None)
        
        drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
        reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
        
        if date_col and drug_col and reaction_col:
            signal_df = df[
                (df[drug_col] == timeline["drug"]) & 
                (df[reaction_col] == timeline["reaction"])
            ]
            
            if not signal_df.empty:
                try:
                    signal_df[date_col] = pd.to_datetime(signal_df[date_col], errors='coerce')
                    signal_df = signal_df.dropna(subset=[date_col])
                    if not signal_df.empty:
                        first_case = signal_df[date_col].min()
                        timeline["first_case_date"] = first_case.isoformat() if hasattr(first_case, 'isoformat') else str(first_case)
                except Exception:
                    pass
    
    # Use provided first case date or signal metadata
    if not timeline["first_case_date"]:
        timeline["first_case_date"] = signal.get("first_case_date", signal.get("first_case", None))
    
    # Process trend alerts
    if trend_alerts:
        timeline["trend_alerts"] = [
            {
                "date": alert.get("date", alert.get("detected_date", None)),
                "type": alert.get("type", alert.get("alert_type", "unknown")),
                "severity": alert.get("severity", alert.get("risk_level", "medium")),
                "description": alert.get("description", alert.get("summary", "")),
                "case_count": alert.get("case_count", alert.get("count", 0))
            }
            for alert in trend_alerts
        ]
        
        # Extract case spikes (high-severity alerts)
        timeline["case_spikes"] = [
            alert for alert in timeline["trend_alerts"]
            if alert.get("severity") in ["high", "critical"] or alert.get("case_count", 0) > 50
        ]
    
    # Process RPF history
    if rpf_history:
        timeline["rpf_scores"] = [
            {
                "date": score.get("date", score.get("timestamp", None)),
                "rpf_score": score.get("rpf_score", score.get("score", 0)),
                "priority": score.get("priority", score.get("risk_level", "unknown")),
                "change_reason": score.get("change_reason", score.get("reason", ""))
            }
            for score in rpf_history
        ]
    else:
        # Create RPF history from signal data
        if signal.get("rpf_score"):
            timeline["rpf_scores"] = [{
                "date": timeline["detection_date"] or timeline["first_case_date"],
                "rpf_score": signal.get("rpf_score"),
                "priority": signal.get("priority", signal.get("risk_level", "unknown")),
                "change_reason": "Initial assessment"
            }]
    
    # Process governance events
    if governance_events:
        timeline["governance_review"] = [
            {
                "date": event.get("date", event.get("timestamp", None)),
                "event_type": event.get("event_type", event.get("type", "unknown")),
                "description": event.get("description", event.get("summary", "")),
                "reviewer": event.get("reviewer", event.get("owner", "Unknown")),
                "status": event.get("status", event.get("state", "unknown"))
            }
            for event in governance_events
        ]
    
    # Extract escalation history from signal or governance events
    if signal.get("status_history"):
        timeline["escalation_history"] = signal["status_history"]
    else:
        # Infer escalation from governance events
        escalation_events = [
            event for event in timeline["governance_review"]
            if event.get("event_type") in ["escalated", "validated", "under_assessment", "closed"]
        ]
        if escalation_events:
            timeline["escalation_history"] = escalation_events
    
    # Regulatory actions from signal metadata
    timeline["regulatory_actions"] = signal.get("regulatory_actions", signal.get("reg_actions", []))
    
    # Label impact events
    timeline["label_impact_events"] = signal.get("label_impact_events", signal.get("label_changes", []))
    
    # Build timeline summary
    timeline["timeline_summary"] = _generate_timeline_summary(timeline)
    
    return timeline


def _generate_timeline_summary(timeline: Dict[str, Any]) -> str:
    """Generate human-readable timeline summary."""
    summary_parts = []
    
    if timeline.get("first_case_date"):
        summary_parts.append(f"First case: {timeline['first_case_date']}")
    
    if timeline.get("detection_date"):
        summary_parts.append(f"Detection: {timeline['detection_date']}")
    
    if timeline.get("case_spikes"):
        summary_parts.append(f"{len(timeline['case_spikes'])} case spike(s) detected")
    
    if timeline.get("trend_alerts"):
        summary_parts.append(f"{len(timeline['trend_alerts'])} trend alert(s)")
    
    if timeline.get("rpf_scores"):
        latest_rpf = timeline["rpf_scores"][-1] if timeline["rpf_scores"] else None
        if latest_rpf:
            summary_parts.append(f"Current RPF: {latest_rpf.get('rpf_score', 'N/A')} ({latest_rpf.get('priority', 'N/A')})")
    
    if timeline.get("escalation_history"):
        summary_parts.append(f"{len(timeline['escalation_history'])} escalation event(s)")
    
    return " | ".join(summary_parts) if summary_parts else "Timeline data available"


def analyze_timeline_gaps(timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze timeline for gaps, delays, and inconsistencies that inspectors would question.
    
    Args:
        timeline: Timeline dictionary from build_signal_timeline()
        
    Returns:
        List of gap/delay findings
    """
    gaps = []
    
    # Check for detection delay
    first_case_date = timeline.get("first_case_date")
    detection_date = timeline.get("detection_date")
    
    if first_case_date and detection_date:
        try:
            first = datetime.fromisoformat(first_case_date.replace("Z", "+00:00"))
            detected = datetime.fromisoformat(detection_date.replace("Z", "+00:00"))
            
            delay_days = (detected - first).days
            if delay_days > 90:
                gaps.append({
                    "type": "detection_delay",
                    "severity": "high" if delay_days > 180 else "medium",
                    "description": f"Signal detected {delay_days} days after first case",
                    "days_delayed": delay_days
                })
        except Exception:
            pass
    
    # Check for escalation delays
    rpf_scores = timeline.get("rpf_scores", [])
    escalation_history = timeline.get("escalation_history", [])
    
    if rpf_scores and escalation_history:
        high_rpf_scores = [s for s in rpf_scores if s.get("rpf_score", 0) >= 70]
        if high_rpf_scores and not escalation_history:
            gaps.append({
                "type": "escalation_delay",
                "severity": "high",
                "description": "High RPF score detected but no escalation recorded",
                "rpf_score": high_rpf_scores[0].get("rpf_score")
            })
    
    # Check for missing governance events
    if timeline.get("first_case_date") and not timeline.get("governance_review"):
        gaps.append({
            "type": "missing_governance",
            "severity": "medium",
            "description": "No governance review events documented for this signal"
        })
    
    # Check for case spikes without response
    case_spikes = timeline.get("case_spikes", [])
    if case_spikes:
        spike_dates = [s.get("date") for s in case_spikes if s.get("date")]
        governance_dates = [g.get("date") for g in timeline.get("governance_review", []) if g.get("date")]
        
        unaddressed_spikes = [s for s in spike_dates if not any(g for g in governance_dates if g and s and abs((datetime.fromisoformat(g.replace("Z", "+00:00")) - datetime.fromisoformat(s.replace("Z", "+00:00"))).days) < 30)]
        
        if unaddressed_spikes:
            gaps.append({
                "type": "unaddressed_spikes",
                "severity": "medium",
                "description": f"{len(unaddressed_spikes)} case spike(s) without documented governance response",
                "spike_count": len(unaddressed_spikes)
            })
    
    return gaps


# Import pandas for date operations
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
