"""
Local Benefit-Risk Visualizer (CHUNK 7.12)
Browser-based benefit-risk analysis visualization.

Based on EMA/FDA BR templates, runs offline via Pyodide.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def render_br_visualizer(
    benefits: Optional[List[Dict[str, Any]]] = None,
    risks: Optional[List[Dict[str, Any]]] = None,
    br_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render benefit-risk visualization panel.
    
    Args:
        benefits: List of benefit data points
        risks: List of risk data points
        br_data: Optional pre-computed BR data
    """
    st.header("⚖️ Benefit-Risk Assessment")
    st.markdown("Visualize benefit-risk trade-offs based on EMA/FDA BR templates.")
    
    # Default data if not provided
    if benefits is None:
        benefits = [
            {"benefit": "Efficacy Endpoint 1", "magnitude": 0.75, "importance": 0.9},
            {"benefit": "Efficacy Endpoint 2", "magnitude": 0.65, "importance": 0.7},
        ]
    
    if risks is None:
        risks = [
            {"risk": "Adverse Event 1", "severity": 0.8, "frequency": 0.3},
            {"risk": "Adverse Event 2", "severity": 0.6, "frequency": 0.5},
        ]
    
    # Benefit magnitude plot
    st.subheader("📈 Benefit Magnitude")
    
    if PANDAS_AVAILABLE:
        benefit_df = pd.DataFrame(benefits)
        
        fig = px.bar(
            benefit_df,
            x='benefit',
            y='magnitude',
            title="Benefit Magnitude by Endpoint",
            labels={'magnitude': 'Benefit Magnitude (0-1)', 'benefit': 'Benefit Endpoint'},
            color='importance',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk severity plots
    st.subheader("⚠️ Risk Severity")
    
    if PANDAS_AVAILABLE:
        risk_df = pd.DataFrame(risks)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=risk_df['risk'],
            y=risk_df['severity'],
            name='Severity',
            marker_color='red'
        ))
        
        fig.add_trace(go.Bar(
            x=risk_df['risk'],
            y=risk_df['frequency'],
            name='Frequency',
            marker_color='orange'
        ))
        
        fig.update_layout(
            title="Risk Severity and Frequency",
            xaxis_title="Risk",
            yaxis_title="Score (0-1)",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # BR trade-off curve
    st.subheader("📊 Benefit-Risk Trade-Off Curve")
    
    # Generate trade-off curve
    benefit_score = sum(b.get('magnitude', 0) * b.get('importance', 0) for b in benefits) / len(benefits) if benefits else 0
    risk_score = sum(r.get('severity', 0) * r.get('frequency', 0) for r in risks) / len(risks) if risks else 0
    
    # Create trade-off visualization
    fig = go.Figure()
    
    # Scatter points for different scenarios
    scenarios = [
        {"name": "Current", "benefit": benefit_score, "risk": risk_score},
        {"name": "Worse Case", "benefit": benefit_score * 0.8, "risk": risk_score * 1.2},
        {"name": "Best Case", "benefit": benefit_score * 1.2, "risk": risk_score * 0.8},
    ]
    
    for scenario in scenarios:
        fig.add_trace(go.Scatter(
            x=[scenario['risk']],
            y=[scenario['benefit']],
            mode='markers+text',
            name=scenario['name'],
            text=[scenario['name']],
            textposition='top center',
            marker=dict(size=15)
        ))
    
    fig.update_layout(
        title="Benefit-Risk Trade-Off Space",
        xaxis_title="Risk Score",
        yaxis_title="Benefit Score",
        height=500,
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk increase forecast slider
    st.subheader("🔮 Risk Increase Forecast")
    st.caption("Adjust risk increase to see impact on benefit-risk balance.")
    
    risk_increase = st.slider(
        "Risk Increase (%)",
        min_value=-50,
        max_value=100,
        value=0,
        step=5,
        help="Simulate increase in risk levels"
    )
    
    adjusted_risk = risk_score * (1 + risk_increase / 100)
    adjusted_br_ratio = benefit_score / adjusted_risk if adjusted_risk > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Adjusted Risk", f"{adjusted_risk:.2f}")
    col2.metric("Benefit Score", f"{benefit_score:.2f}")
    col3.metric("B/R Ratio", f"{adjusted_br_ratio:.2f}", 
                delta=f"{adjusted_br_ratio - (benefit_score / risk_score if risk_score > 0 else 0):.2f}" if risk_score > 0 else None)
    
    # Decision framework
    st.subheader("🎯 Decision Framework")
    
    if adjusted_br_ratio > 1.5:
        st.success("✅ **Positive Benefit-Risk Profile** - Benefits clearly outweigh risks.")
    elif adjusted_br_ratio > 1.0:
        st.warning("⚠️ **Favorable Benefit-Risk Profile** - Benefits outweigh risks with monitoring recommended.")
    elif adjusted_br_ratio > 0.7:
        st.warning("⚠️ **Uncertain Benefit-Risk Profile** - Requires careful evaluation and risk mitigation.")
    else:
        st.error("❌ **Negative Benefit-Risk Profile** - Risks may outweigh benefits. Re-evaluation required.")
    
    # Export options
    with st.expander("💾 Export BR Analysis"):
        st.download_button(
            label="📥 Download BR Report",
            data=_generate_br_report(benefits, risks, benefit_score, risk_score, adjusted_br_ratio),
            file_name="benefit_risk_analysis.txt",
            mime="text/plain"
        )


def _generate_br_report(benefits: List[Dict], risks: List[Dict], benefit_score: float, risk_score: float, br_ratio: float) -> str:
    """Generate text report for download."""
    report = f"""
BENEFIT-RISK ASSESSMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

BENEFIT SUMMARY
"""
    for benefit in benefits:
        report += f"- {benefit.get('benefit', 'Unknown')}: {benefit.get('magnitude', 0):.2f}\n"
    
    report += f"\nOverall Benefit Score: {benefit_score:.2f}\n\n"
    
    report += "RISK SUMMARY\n"
    for risk in risks:
        report += f"- {risk.get('risk', 'Unknown')}: Severity {risk.get('severity', 0):.2f}, Frequency {risk.get('frequency', 0):.2f}\n"
    
    report += f"\nOverall Risk Score: {risk_score:.2f}\n\n"
    
    report += f"BENEFIT-RISK RATIO: {br_ratio:.2f}\n"
    
    return report

