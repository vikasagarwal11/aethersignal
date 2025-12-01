"""
Oversight Metrics Panel (CHUNK A3.2)
Displays governance oversight metrics and KPIs.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd


def render_oversight_metrics(
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    governance_gaps: Optional[Dict[str, Any]] = None,
    capa_findings: Optional[Dict[str, Any]] = None,
    timing_deviations: Optional[Dict[str, Any]] = None,
    lifecycle_stage: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render oversight metrics panel.
    
    Args:
        trend_alerts: List of trend alert dictionaries
        governance_gaps: Governance gap findings
        capa_findings: CAPA findings
        timing_deviations: Timing compliance deviations
        lifecycle_stage: Lifecycle stage information
    """
    st.subheader("📈 Oversight Metrics")
    
    trend_alerts = trend_alerts or []
    governance_gaps = governance_gaps or {}
    capa_findings = capa_findings or {}
    timing_deviations = timing_deviations or {}
    lifecycle_stage = lifecycle_stage or {}
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Trend Alerts", len(trend_alerts))
        if trend_alerts:
            high_severity = sum(1 for a in trend_alerts if isinstance(a, dict) and a.get("severity") in ["high", "critical", "warning"])
            st.caption(f"{high_severity} high severity")
    
    with col2:
        timing_late = timing_deviations.get("late_items", 0) or timing_deviations.get("overdue_count", 0)
        st.metric("Timing Deviations", timing_late, 
                 delta=f"{timing_late} overdue" if timing_late > 0 else "On time",
                 delta_color="inverse" if timing_late > 0 else "normal")
    
    with col3:
        open_major = capa_findings.get("open_major", 0) or capa_findings.get("urgent_capa_count", 0)
        open_minor = capa_findings.get("open_minor", 0) or (capa_findings.get("total_capa", 0) - open_major)
        st.metric("Open CAPA (Major)", open_major)
        st.caption(f"{open_minor} minor items")
    
    with col4:
        gaps_count = governance_gaps.get("gaps_count", 0) or governance_gaps.get("major_gaps", 0) or governance_gaps.get("minor_gaps", 0)
        st.metric("Governance Gaps", gaps_count)
        if gaps_count > 0:
            st.caption("Action required")
    
    st.markdown("---")
    
    # Signal Lifecycle Stage
    st.markdown("### 🔄 Signal Lifecycle Stage")
    stage = lifecycle_stage.get("stage", "Unknown") if isinstance(lifecycle_stage, dict) else str(lifecycle_stage) if lifecycle_stage else "Unknown"
    st.info(f"**Current Stage:** {stage}")
    
    if isinstance(lifecycle_stage, dict):
        evidence = lifecycle_stage.get("evidence")
        if evidence:
            st.caption(f"Evidence: {evidence}")
        
        ai_rationale = lifecycle_stage.get("ai_rationale")
        if ai_rationale:
            with st.expander("🤖 AI Rationale", expanded=False):
                st.markdown(ai_rationale)
    
    # Compliance Score
    st.markdown("---")
    st.markdown("### 📊 Compliance Overview")
    
    compliance_score = governance_gaps.get("compliance_score", 100)
    if isinstance(compliance_score, (int, float)):
        score_color = "🟢" if compliance_score >= 80 else "🟡" if compliance_score >= 60 else "🔴"
        st.metric("Overall Compliance Score", f"{compliance_score:.1f}/100", delta=None, delta_color="normal")
        st.caption(f"{score_color} {'Good' if compliance_score >= 80 else 'Needs Improvement' if compliance_score >= 60 else 'Critical'}")
    
    # Trend Alert Summary
    if trend_alerts:
        st.markdown("---")
        st.markdown("### ⚠️ Trend Alert Summary")
        
        alert_summary = {}
        for alert in trend_alerts:
            if isinstance(alert, dict):
                severity = alert.get("severity", "info")
                alert_summary[severity] = alert_summary.get(severity, 0) + 1
        
        if alert_summary:
            summary_df = pd.DataFrame({
                "Severity": list(alert_summary.keys()),
                "Count": list(alert_summary.values())
            })
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

