"""
Executive Safety Dashboard (CHUNK 6.30)
High-level executive dashboard showing portfolio-level KPIs and trends.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def render_executive_dashboard(
    stats: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    alerts: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None
) -> None:
    """
    Render executive safety dashboard.
    
    Args:
        stats: Optional statistics dictionary
        trends: Optional trends data
        alerts: Optional list of alerts
        df: Optional DataFrame for calculating metrics
    """
    st.title("🏢 Executive Safety Dashboard")
    st.markdown("Portfolio-level safety intelligence and key performance indicators.")
    
    # Calculate stats from DataFrame if not provided
    if stats is None:
        stats = _calculate_stats(df)
    
    if alerts is None:
        alerts = _get_alerts(df)
    
    # Top-level KPIs
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_cases = stats.get("total_cases", 0)
    open_signals = stats.get("open_signals", 0)
    high_alerts = stats.get("high_alerts", len([a for a in alerts if a.get("severity") == "high"]))
    serious_cases = stats.get("serious_cases", 0)
    compliance_score = stats.get("compliance_score", 0)
    
    col1.metric("Total Cases", f"{total_cases:,}")
    col2.metric("Open Signals", open_signals)
    col3.metric("High Alerts", high_alerts, delta=f"-{max(0, high_alerts - 5)}" if high_alerts > 5 else None)
    col4.metric("Serious Cases", f"{serious_cases:,}", delta=f"{serious_cases / max(total_cases, 1) * 100:.1f}%")
    col5.metric("Compliance Score", f"{compliance_score:.0f}%", delta="+2%" if compliance_score > 90 else None)
    
    st.markdown("---")
    
    # Portfolio Risk Heatmap
    st.subheader("🔥 Portfolio Risk Heatmap")
    st.caption("Risk levels across drug-reaction combinations.")
    
    risk_matrix = stats.get("risk_matrix")
    if risk_matrix is not None and not risk_matrix.empty:
        fig = px.imshow(
            risk_matrix,
            aspect="auto",
            color_continuous_scale="Reds",
            title="Portfolio Risk Heatmap",
            labels=dict(color="Risk Level")
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Generate risk matrix from signal data to display heatmap.")
    
    st.markdown("---")
    
    # Top Risks
    st.subheader("⚠️ Top Safety Concerns")
    
    if alerts:
        # Display top 10 alerts
        for i, alert in enumerate(alerts[:10], 1):
            severity = alert.get("severity", "medium")
            severity_color = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity, "⚪")
            
            with st.expander(f"{severity_color} #{i}: {alert.get('title', 'Unknown Alert')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Drug:** {alert.get('drug', 'Unknown')}")
                    st.write(f"**Reaction:** {alert.get('reaction', 'Unknown')}")
                with col2:
                    st.write(f"**Severity:** {severity.upper()}")
                    st.write(f"**Cases:** {alert.get('case_count', 0):,}")
                
                if alert.get("description"):
                    st.write(f"**Description:** {alert.get('description')}")
    else:
        st.info("No alerts available. Upload data and run analysis to see safety concerns.")
    
    st.markdown("---")
    
    # Trends over time
    st.subheader("📈 Trends Over Time")
    
    if trends:
        trend_data = trends.get("monthly_cases")
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            fig = px.line(
                trend_df,
                x="month",
                y="cases",
                title="Monthly Case Volume Trend",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Generate trend data to display time-series charts.")
    
    st.markdown("---")
    
    # Governance Metrics
    st.subheader("🛡️ Governance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Signals Under Review", stats.get("signals_under_review", 0))
    col2.metric("Overdue Signals", stats.get("overdue_signals", 0))
    col3.metric("Avg Review Time", f"{stats.get('avg_review_time_days', 0):.0f} days")
    col4.metric("Reviewer Capacity", f"{stats.get('reviewer_capacity', 0)}%")
    
    st.markdown("---")
    
    # Summary Narrative
    st.subheader("📝 Executive Summary")
    
    summary = _generate_executive_summary(stats, alerts)
    st.markdown(summary)
    
    # Export options
    with st.expander("💾 Export Dashboard"):
        st.download_button(
            label="📥 Download Dashboard Report (PDF)",
            data=_generate_dashboard_report(stats, alerts),
            file_name=f"executive_dashboard_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )


def _calculate_stats(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Calculate statistics from DataFrame."""
    if df is None or df.empty:
        return {
            "total_cases": 0,
            "open_signals": 0,
            "high_alerts": 0,
            "serious_cases": 0,
            "compliance_score": 0,
        }
    
    # Find relevant columns
    drug_col = _find_column(df, ["drug", "drug_name", "DRUG"])
    reaction_col = _find_column(df, ["reaction", "reaction_pt", "PT", "REACTION"])
    serious_col = _find_column(df, ["serious", "SERIOUS", "seriousness"])
    
    total_cases = len(df)
    serious_cases = 0
    
    if serious_col:
        serious_cases = df[serious_col].sum() if df[serious_col].dtype in [bool, 'int64'] else len(df[df[serious_col].notna()])
    
    # Count unique signals
    if drug_col and reaction_col:
        unique_signals = df[[drug_col, reaction_col]].drop_duplicates().shape[0]
    else:
        unique_signals = 0
    
    return {
        "total_cases": total_cases,
        "open_signals": unique_signals,
        "high_alerts": 0,  # Would come from trend alerts
        "serious_cases": serious_cases,
        "compliance_score": 85,  # Placeholder
        "signals_under_review": 0,
        "overdue_signals": 0,
        "avg_review_time_days": 0,
        "reviewer_capacity": 0,
    }


def _get_alerts(df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
    """Get alerts from DataFrame."""
    if df is None or df.empty:
        return []
    
    # Placeholder - would come from trend alerts engine
    return []


def _find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """Find column by possible names."""
    for name in possible_names:
        if name in df.columns:
            return name
    return None


def _generate_executive_summary(stats: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
    """Generate executive summary text."""
    total_cases = stats.get("total_cases", 0)
    open_signals = stats.get("open_signals", 0)
    high_alerts = len([a for a in alerts if a.get("severity") == "high"])
    
    summary = f"""
### Current Status
    
- **Total Cases:** {total_cases:,} cases in portfolio
- **Active Signals:** {open_signals} signals under management
- **High-Priority Alerts:** {high_alerts} alerts requiring immediate attention

### Key Observations

This dashboard provides a high-level view of safety intelligence across the portfolio.
For detailed analysis, navigate to specific signal assessments or trend analysis tabs.

### Recommended Actions

1. Review high-priority alerts for immediate safety concerns
2. Monitor portfolio risk heatmap for emerging patterns
3. Track governance metrics to ensure compliance
4. Review trend data for temporal patterns
"""
    return summary


def _generate_dashboard_report(stats: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
    """Generate text report for download."""
    report = f"""
EXECUTIVE SAFETY DASHBOARD REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

KEY METRICS
- Total Cases: {stats.get('total_cases', 0):,}
- Open Signals: {stats.get('open_signals', 0)}
- High Alerts: {len([a for a in alerts if a.get('severity') == 'high'])}
- Compliance Score: {stats.get('compliance_score', 0):.0f}%

TOP ALERTS
"""
    for i, alert in enumerate(alerts[:10], 1):
        report += f"{i}. {alert.get('title', 'Unknown')} - {alert.get('severity', 'Unknown')}\n"
    
    return report

