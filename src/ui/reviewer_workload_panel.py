"""
Reviewer Workload Forecast Panel (CHUNK B6)
UI for displaying reviewer workload forecasts and load balancing.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.ai.reviewer_workload_forecaster import (
        forecast_reviewer_workload,
        generate_workload_forecast_summary
    )
    FORECASTER_AVAILABLE = True
except ImportError:
    FORECASTER_AVAILABLE = False


def render_reviewer_workload_panel(
    reviewers_df: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    forecast_days: int = 30
) -> None:
    """
    Render reviewer workload forecast panel (CHUNK B6).
    
    Args:
        reviewers_df: DataFrame with reviewer information
        signals: List of signal dictionaries
        forecast_days: Number of days to forecast ahead
    """
    if not FORECASTER_AVAILABLE:
        st.error("Reviewer Workload Forecaster not available. Please install required dependencies.")
        return
    
    st.subheader("👥 Reviewer Workload Forecast")
    
    if reviewers_df is None or reviewers_df.empty:
        st.warning("No reviewer data available. Please configure reviewers first.")
        return
    
    if not signals:
        st.warning("No signals available for workload analysis.")
        return
    
    # Forecast horizon selection
    forecast_days = st.slider(
        "Forecast Horizon (days)",
        7,
        90,
        forecast_days,
        step=7,
        help="Number of days ahead to forecast workload"
    )
    
    # Generate forecast
    with st.spinner("Computing workload forecast..."):
        forecast_df = forecast_reviewer_workload(
            reviewers_df=reviewers_df,
            signals=signals,
            forecast_days=forecast_days
        )
    
    if forecast_df is None or forecast_df.empty:
        st.warning("Could not generate workload forecast.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reviewers", len(forecast_df))
    
    with col2:
        critical_count = len(forecast_df[forecast_df["capacity_risk"] == "Critical"])
        st.metric("Critical Risk", critical_count, delta=f"{critical_count} overloaded" if critical_count > 0 else None, delta_color="inverse")
    
    with col3:
        total_overdue = forecast_df["overdue_count"].sum()
        st.metric("Total Overdue", total_overdue, delta="Action Required" if total_overdue > 0 else None, delta_color="inverse")
    
    with col4:
        total_rls = forecast_df["risk_load_score"].sum()
        avg_rls = total_rls / len(forecast_df) if len(forecast_df) > 0 else 0
        st.metric("Avg Risk Load", f"{avg_rls:.1f}")
    
    st.markdown("---")
    
    # Reviewer Forecast Table (B6.2)
    st.markdown("### 📊 Reviewer Workload Table")
    
    # Sort by risk load score (highest first)
    display_df = forecast_df.sort_values("risk_load_score", ascending=False)
    
    # Color code by capacity risk
    def color_capacity_risk(val):
        if val == "Critical":
            return "background-color: #ffcccc"
        elif val == "High":
            return "background-color: #fff4cc"
        elif val == "Medium":
            return "background-color: #e6f4ea"
        else:
            return "background-color: #f0f0f0"
    
    styled_df = display_df.style.applymap(color_capacity_risk, subset=["capacity_risk"])
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Workload Forecast Chart (B6.3)
    if PLOTLY_AVAILABLE:
        st.markdown("---")
        st.markdown("### 📈 Workload Forecast Chart")
        
        fig = px.bar(
            display_df,
            x="name",
            y="risk_load_score",
            color="risk_load_score",
            title="Reviewer Workload Forecast (Risk-Weighted)",
            labels={"risk_load_score": "Risk Load Score (RLS)", "name": "Reviewer"},
            color_continuous_scale="Reds"
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Capacity Risk Distribution
        st.markdown("### 🎯 Capacity Risk Distribution")
        
        risk_counts = forecast_df["capacity_risk"].value_counts()
        
        fig2 = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="Reviewers by Capacity Risk Level",
            color_discrete_map={
                "Critical": "#DC2626",
                "High": "#F59E0B",
                "Medium": "#10B981",
                "Low": "#6B7280"
            }
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # AI-Generated Forecast Summary (B6.4)
    st.markdown("---")
    st.markdown("### 🤖 Workload Forecast Summary")
    
    with st.spinner("Generating AI workload analysis..."):
        summary = generate_workload_forecast_summary(forecast_df)
        st.markdown(summary)
    
    # Export option
    st.markdown("---")
    st.markdown("### 💾 Export Forecast")
    csv = forecast_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Workload Forecast (CSV)",
        data=csv,
        file_name=f"reviewer_workload_forecast_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

