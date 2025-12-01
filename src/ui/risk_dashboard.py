"""
Global Risk Dashboard UI (Phase 3F.5)
Interactive dashboard for risk management and prioritization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.risk.global_risk_manager import GlobalRiskManager
from src.risk.rmp_generator import RMPGenerator

logger = logging.getLogger(__name__)


def render_risk_dashboard(df: Optional[pd.DataFrame] = None):
    """
    Render global risk dashboard.
    
    Args:
        df: Optional DataFrame with AE entries
    """
    st.header("⚠️ Global Risk Management Dashboard")
    st.caption("Multi-factor risk scoring, prioritization, and regulatory recommendations")
    
    if df is None or df.empty:
        st.info("👆 Load AE data first")
        return
    
    # Initialize risk manager
    risk_manager = GlobalRiskManager()
    rmp_generator = RMPGenerator()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Risk Prioritization",
        "📈 Risk Quadrant",
        "📄 RMP Generator",
        "🔄 Escalation Workflow",
        "📊 Severity/Novelty Matrix"
    ])
    
    with tab1:
        render_risk_prioritization_tab(df, risk_manager)
    
    with tab2:
        render_risk_quadrant_tab(df, risk_manager)
    
    with tab3:
        render_rmp_generator_tab(df, risk_manager, rmp_generator)
    
    with tab4:
        render_escalation_workflow_tab()
    
    with tab5:
        render_severity_novelty_matrix_tab(df, risk_manager)


def render_risk_prioritization_tab(df: pd.DataFrame, risk_manager: GlobalRiskManager):
    """Render risk prioritization tab."""
    st.subheader("📊 Risk Prioritization")
    
    # Drug filter
    drug_filter = st.text_input("Filter by Drug (optional)", "")
    
    # Prioritize signals
    if st.button("🔍 Prioritize Signals", type="primary"):
        with st.spinner("Calculating Global Risk Index for all signals..."):
            prioritized = risk_manager.prioritize_signals(
                df,
                drug=drug_filter if drug_filter else None,
                limit=50
            )
            
            if prioritized:
                st.session_state["prioritized_signals"] = prioritized
                st.success(f"✅ Prioritized {len(prioritized)} signals")
            else:
                st.warning("⚠️ No signals found")
    
    # Display prioritized signals
    if "prioritized_signals" in st.session_state:
        signals = st.session_state["prioritized_signals"]
        
        # Filter by priority category
        category_filter = st.multiselect(
            "Filter by Priority",
            options=["critical", "high", "moderate", "low", "minimal"],
            default=["critical", "high", "moderate"]
        )
        
        filtered_signals = [
            s for s in signals
            if s.get("priority_category") in category_filter
        ]
        
        # Create DataFrame
        signals_df = pd.DataFrame([
            {
                "Drug": s.get("drug"),
                "Reaction": s.get("reaction"),
                "GRI Score": s.get("gri_score", 0.0),
                "Priority": s.get("priority_category", "unknown").title(),
                "Action": s.get("recommended_action", "monitor").replace("_", " ").title(),
                "Cases": s.get("total_cases", 0)
            }
            for s in filtered_signals
        ])
        
        st.dataframe(signals_df, use_container_width=True, height=500)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            critical = len([s for s in filtered_signals if s.get("priority_category") == "critical"])
            st.metric("Critical", critical)
        with col2:
            high = len([s for s in filtered_signals if s.get("priority_category") == "high"])
            st.metric("High", high)
        with col3:
            moderate = len([s for s in filtered_signals if s.get("priority_category") == "moderate"])
            st.metric("Moderate", moderate)
        with col4:
            avg_gri = sum(s.get("gri_score", 0) for s in filtered_signals) / len(filtered_signals) if filtered_signals else 0
            st.metric("Avg GRI", f"{avg_gri:.2f}")


def render_risk_quadrant_tab(df: pd.DataFrame, risk_manager: GlobalRiskManager):
    """Render risk quadrant visualization."""
    st.subheader("📈 Risk Quadrant (Novelty × Severity)")
    
    if "prioritized_signals" not in st.session_state:
        st.info("👆 Prioritize signals first")
        return
    
    signals = st.session_state["prioritized_signals"]
    
    # Extract novelty and severity
    quadrant_data = []
    for signal in signals:
        components = signal.get("components", {})
        novelty = components.get("novelty_label_gaps", 0.0)
        severity = components.get("severity_seriousness", 0.0)
        gri = signal.get("gri_score", 0.0)
        
        quadrant_data.append({
            "drug": signal.get("drug"),
            "reaction": signal.get("reaction"),
            "novelty": novelty,
            "severity": severity,
            "gri": gri,
            "priority": signal.get("priority_category", "low")
        })
    
    if quadrant_data:
        quadrant_df = pd.DataFrame(quadrant_data)
        
        # Create scatter plot
        fig = px.scatter(
            quadrant_df,
            x="novelty",
            y="severity",
            size="gri",
            color="priority",
            hover_data=["drug", "reaction", "gri"],
            title="Risk Quadrant: Novelty vs Severity",
            labels={"novelty": "Novelty Score", "severity": "Severity Score"},
            color_discrete_map={
                "critical": "red",
                "high": "orange",
                "moderate": "yellow",
                "low": "lightblue",
                "minimal": "gray"
            }
        )
        
        # Add quadrant lines
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Severity Threshold")
        fig.add_vline(x=0.5, line_dash="dash", line_color="gray", annotation_text="Novelty Threshold")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Quadrant summary
        st.markdown("### Quadrant Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**New + Severe (Critical Zone)**")
            critical_zone = quadrant_df[
                (quadrant_df["novelty"] >= 0.5) & (quadrant_df["severity"] >= 0.5)
            ]
            st.write(f"Signals: {len(critical_zone)}")
        with col2:
            st.markdown("**Known + Non-Severe (Low Risk)**")
            low_zone = quadrant_df[
                (quadrant_df["novelty"] < 0.5) & (quadrant_df["severity"] < 0.5)
            ]
            st.write(f"Signals: {len(low_zone)}")


def render_rmp_generator_tab(
    df: pd.DataFrame,
    risk_manager: GlobalRiskManager,
    rmp_generator: RMPGenerator
):
    """Render RMP generator tab."""
    st.subheader("📄 RMP Generator")
    
    if "prioritized_signals" not in st.session_state:
        st.info("👆 Prioritize signals first")
        return
    
    signals = st.session_state["prioritized_signals"]
    
    # Select signal
    signal_options = [
        f"{s.get('drug')} → {s.get('reaction')} (GRI: {s.get('gri_score', 0):.2f})"
        for s in signals[:20]  # Top 20
    ]
    
    selected = st.selectbox("Select Signal", options=signal_options)
    
    if selected and st.button("📄 Generate RMP Section"):
        # Find selected signal
        idx = signal_options.index(selected)
        signal = signals[idx]
        
        drug = signal.get("drug")
        reaction = signal.get("reaction")
        
        # Generate RMP section
        with st.spinner("Generating RMP section..."):
            rmp_section = rmp_generator.generate_rmp_section(
                drug,
                reaction,
                signal
            )
            
            st.session_state["rmp_section"] = rmp_section
    
    # Display RMP section
    if "rmp_section" in st.session_state:
        rmp = st.session_state["rmp_section"]
        
        st.markdown("### RMP Section")
        
        st.markdown("#### Summary")
        st.write(rmp.get("summary", ""))
        
        st.markdown("#### Epidemiological Statistics")
        stats = rmp.get("epidemiological_stats", {})
        st.json(stats)
        
        st.markdown("#### Mechanistic Justification")
        st.write(rmp.get("mechanistic_justification", ""))
        
        st.markdown("#### Recommended Actions")
        actions = rmp.get("recommended_actions", [])
        for action in actions:
            st.write(f"- {action}")
        
        st.markdown("#### Monitoring Plan")
        st.write(rmp.get("monitoring_plan", ""))
        
        st.markdown("#### Mitigation Plan")
        st.write(rmp.get("mitigation_plan", ""))
        
        # Export options
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("📄 Download PDF", "PDF export coming soon", disabled=True)
        with col2:
            st.download_button("📊 Download JSON", str(rmp).encode(), file_name="rmp_section.json")
        with col3:
            st.download_button("📝 Download Word", "Word export coming soon", disabled=True)


def render_escalation_workflow_tab():
    """Render escalation workflow tab."""
    st.subheader("🔄 Safety Escalation Workflow")
    st.info("💡 Enterprise feature - Track signal review status and assignments")
    
    # Placeholder for escalation workflow
    st.write("Coming soon: Signal review workflow, status tracking, and assignment management")


def render_severity_novelty_matrix_tab(df: pd.DataFrame, risk_manager: GlobalRiskManager):
    """Render severity/novelty matrix."""
    st.subheader("📊 Severity/Novelty Matrix")
    
    if "prioritized_signals" not in st.session_state:
        st.info("👆 Prioritize signals first")
        return
    
    signals = st.session_state["prioritized_signals"]
    
    # Create matrix data
    matrix_data = []
    for signal in signals:
        components = signal.get("components", {})
        matrix_data.append({
            "novelty": components.get("novelty_label_gaps", 0.0),
            "severity": components.get("severity_seriousness", 0.0),
            "volume": signal.get("total_cases", 0),
            "trend": components.get("trend_burst", 0.0),
            "drug": signal.get("drug"),
            "reaction": signal.get("reaction")
        })
    
    if matrix_data:
        matrix_df = pd.DataFrame(matrix_data)
        
        # Create heatmap
        fig = px.density_heatmap(
            matrix_df,
            x="novelty",
            y="severity",
            z="volume",
            title="Severity × Novelty Matrix",
            labels={"novelty": "Novelty Score", "severity": "Severity Score", "volume": "Case Volume"}
        )
        
        st.plotly_chart(fig, use_container_width=True)

