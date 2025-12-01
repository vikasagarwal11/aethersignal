"""
Heatmap Data Population Logic (CHUNK A2)
Converts analytics outputs (trend alerts, RPF, SHMI, etc.) into risk levels
for heatmap visualization.
"""
import pandas as pd
from typing import Dict, List, Any, Optional


def to_level(value: Optional[float], thresholds: Dict[str, float]) -> str:
    """
    Generic risk-level converter.
    
    Args:
        value: Numeric value to classify
        thresholds: Dict with "low" and "medium" threshold values
        
    Returns:
        Risk level: "Low", "Medium", "High", or "N/A"
    """
    if value is None:
        return "N/A"
    
    if value < thresholds.get("low", 0.3):
        return "Low"
    elif value < thresholds.get("medium", 0.6):
        return "Medium"
    else:
        return "High"


def build_heatmap_levels(
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    rpf_scores: Optional[Dict[str, Any]] = None,
    confidence_scores: Optional[Dict[str, Any]] = None,
    label_impact_scores: Optional[Dict[str, Any]] = None,
    subgroup_scores: Optional[List[Dict[str, Any]]] = None,
    shmi_score: Optional[Dict[str, Any]] = None,
    governance_gaps: Optional[Dict[str, Any]] = None,
    timing_deviations: Optional[Dict[str, Any]] = None,
    lifecycle_stage: Optional[Dict[str, Any]] = None,
    capa_findings: Optional[Dict[str, Any]] = None,
    signal_name: str = "Current Signal"
) -> pd.DataFrame:
    """
    Convert analytics into risk-level values (Low/Medium/High/N/A).
    
    Args:
        trend_alerts: List of trend alert dictionaries
        rpf_scores: Risk Prioritization Framework scores
        confidence_scores: Signal Confidence Scores
        label_impact_scores: Label impact assessment scores
        subgroup_scores: Subgroup analysis results
        shmi_score: Signal Health Maturity Index
        governance_gaps: Governance gap findings
        timing_deviations: Timing compliance deviations
        lifecycle_stage: Lifecycle stage information
        capa_findings: CAPA findings
        signal_name: Name/label for the signal row
        
    Returns:
        DataFrame with risk levels for heatmap visualization
    """
    trend_alerts = trend_alerts or []
    rpf_scores = rpf_scores or {}
    confidence_scores = confidence_scores or {}
    label_impact_scores = label_impact_scores or {}
    subgroup_scores = subgroup_scores or []
    shmi_score = shmi_score or {}
    governance_gaps = governance_gaps or {}
    timing_deviations = timing_deviations or {}
    lifecycle_stage = lifecycle_stage or {}
    capa_findings = capa_findings or {}
    
    # --- Trend Severity ---
    trend_levels = []
    for alert in trend_alerts:
        severity = alert.get("severity", "info") if isinstance(alert, dict) else "info"
        if severity in ["critical", "high", "warning"]:
            trend_levels.append("High")
        elif severity in ["medium", "info"]:
            trend_levels.append("Medium")
        else:
            trend_levels.append("Low")
    
    if not trend_levels:
        trend_level = "N/A"
    elif "High" in trend_levels:
        trend_level = "High"
    elif "Medium" in trend_levels:
        trend_level = "Medium"
    else:
        trend_level = "Low"
    
    # --- RPF (Risk Priority Framework) ---
    rpf_score_value = rpf_scores.get("rpf_score") or rpf_scores.get("qsp_score") or rpf_scores.get("priority_index")
    if rpf_score_value is not None:
        rpf_level = to_level(
            float(rpf_score_value) / 100.0 if rpf_score_value > 1 else float(rpf_score_value),
            {"low": 0.3, "medium": 0.6}
        )
    else:
        rpf_priority = rpf_scores.get("priority", rpf_scores.get("qsp_priority", "")).lower()
        if rpf_priority in ["high", "critical"]:
            rpf_level = "High"
        elif rpf_priority == "medium":
            rpf_level = "Medium"
        else:
            rpf_level = "Low"
    
    # --- Confidence Score ---
    confidence_value = confidence_scores.get("overall_confidence") or confidence_scores.get("score")
    if confidence_value is not None:
        confidence_level = to_level(
            float(confidence_value) / 100.0 if confidence_value > 1 else float(confidence_value),
            {"low": 0.4, "medium": 0.7}
        )
    else:
        confidence_level = "N/A"
    
    # --- Label Impact ---
    label_impact_value = label_impact_scores.get("impact_score") or label_impact_scores.get("score")
    if label_impact_value is not None:
        label_level = to_level(
            float(label_impact_value),
            {"low": 0.3, "medium": 0.6}
        )
    else:
        should_update = label_impact_scores.get("should_update_label", False)
        label_level = "High" if should_update else "Low"
    
    # --- Subgroup signals ---
    if subgroup_scores and len(subgroup_scores) > 0:
        high_sig = any(
            s.get("significance") == "high" or s.get("prr", 0) > 2.0
            for s in subgroup_scores if isinstance(s, dict)
        )
        medium_sig = any(
            s.get("significance") == "medium" or (s.get("prr", 0) > 1.5 and s.get("prr", 0) <= 2.0)
            for s in subgroup_scores if isinstance(s, dict)
        )
        
        if high_sig:
            subgroup_level = "High"
        elif medium_sig:
            subgroup_level = "Medium"
        else:
            subgroup_level = "Low"
    else:
        subgroup_level = "N/A"
    
    # --- SHMI Score (0–100) ---
    shmi_value = shmi_score.get("shmi_score") or shmi_score.get("shmi_value")
    if shmi_value is not None:
        shmi_level = to_level(
            float(shmi_value) / 100.0,
            {"low": 0.4, "medium": 0.7}
        )
    else:
        shmi_level = "N/A"
    
    # --- Governance Gaps ---
    major_gaps = governance_gaps.get("major_gaps", 0) or governance_gaps.get("critical_gaps", 0)
    minor_gaps = governance_gaps.get("minor_gaps", 0) or governance_gaps.get("gaps_count", 0)
    
    if major_gaps > 0:
        gov_level = "High"
    elif minor_gaps > 0:
        gov_level = "Medium"
    else:
        gov_level = "Low"
    
    # --- Timing Deviations ---
    late_items = timing_deviations.get("late_items", 0) or timing_deviations.get("overdue_count", 0)
    
    if late_items > 3:
        timing_level = "High"
    elif late_items > 0:
        timing_level = "Medium"
    else:
        timing_level = "Low"
    
    # --- Lifecycle Stage ---
    stage = lifecycle_stage.get("stage", "").lower() if isinstance(lifecycle_stage, dict) else str(lifecycle_stage).lower()
    
    if stage in ["escalated", "validated", "new_signal", "critical"]:
        lifecycle_level = "High"
    elif stage in ["monitoring", "under_review", "assessment", "evaluation"]:
        lifecycle_level = "Medium"
    elif stage in ["closed", "archived"]:
        lifecycle_level = "Low"
    else:
        lifecycle_level = "N/A"
    
    # --- CAPA Findings ---
    open_major = capa_findings.get("open_major", 0) or capa_findings.get("urgent_capa_count", 0)
    open_minor = capa_findings.get("open_minor", 0) or capa_findings.get("total_capa", 0)
    
    if open_major > 0:
        capa_level = "High"
    elif open_minor > 0:
        capa_level = "Medium"
    else:
        capa_level = "Low"
    
    # Build DataFrame
    df = pd.DataFrame({
        "Trend Severity": [trend_level],
        "RPF Priority": [rpf_level],
        "Confidence Score": [confidence_level],
        "Label Impact": [label_level],
        "Subgroup Risk": [subgroup_level],
        "SHMI Maturity": [shmi_level],
        "Governance Completeness": [gov_level],
        "Timing Compliance": [timing_level],
        "Lifecycle Stage": [lifecycle_level],
        "CAPA Requirement": [capa_level],
    }, index=[signal_name])
    
    return df

