"""
Local Trend Panel (CHUNK 7.10 UI)
UI component for displaying local trend analysis results.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

try:
    from src.local_engine.local_trend_engine import LocalTrendEngine
    TREND_ENGINE_AVAILABLE = True
except ImportError:
    TREND_ENGINE_AVAILABLE = False


def render_local_trend_panel(df: Optional[pd.DataFrame] = None, trend_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Render local trend analysis panel.
    
    Args:
        df: Optional DataFrame (will analyze if provided and trend_data not available)
        trend_data: Optional pre-computed trend data
    """
    if not TREND_ENGINE_AVAILABLE:
        st.error("Local trend engine not available.")
        return
    
    st.header("📈 Local Trend Analysis")
    st.markdown("Browser-based trend analysis with spike detection and emerging pattern identification.")
    
    # Analyze trends if data provided
    if trend_data is None and df is not None and not df.empty:
        with st.spinner("Analyzing trends locally..."):
            engine = LocalTrendEngine()
            trend_data = engine.analyze_trends(df)
    
    if not trend_data or trend_data.get("error"):
        if df is None or df.empty:
            st.info("Upload data to perform trend analysis.")
        else:
            st.error(f"Trend analysis failed: {trend_data.get('error', 'Unknown error')}")
        return
    
    # Display monthly counts
    monthly_counts = trend_data.get("monthly_counts", [])
    if monthly_counts:
        st.subheader("📊 Monthly Case Volume")
        
        # Create trend chart
        trend_df = pd.DataFrame(monthly_counts)
        
        fig = go.Figure()
        
        # Add monthly counts
        fig.add_trace(go.Scatter(
            x=trend_df['year_month'],
            y=trend_df['count'],
            mode='lines+markers',
            name='Monthly Cases',
            line=dict(color='blue', width=2)
        ))
        
        # Add moving average
        moving_avg = trend_data.get("moving_average", [])
        if moving_avg and len(moving_avg) == len(trend_df):
            fig.add_trace(go.Scatter(
                x=trend_df['year_month'],
                y=moving_avg,
                mode='lines',
                name=f'{engine.window_months if "engine" in locals() else 3}-Month Moving Average',
                line=dict(color='orange', width=2, dash='dash')
            ))
        
        # Mark spikes
        spikes = trend_data.get("spikes", [])
        if spikes:
            spike_periods = [s['period'] for s in spikes]
            spike_values = [s['value'] for s in spikes]
            
            fig.add_trace(go.Scatter(
                x=spike_periods,
                y=spike_values,
                mode='markers',
                name='Spikes',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='triangle-up'
                )
            ))
        
        fig.update_layout(
            title="Case Volume Trend with Spike Detection",
            xaxis_title="Month",
            yaxis_title="Number of Cases",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display spikes
    spikes = trend_data.get("spikes", [])
    if spikes:
        st.subheader("⚠️ Detected Spikes")
        st.caption(f"Found {len(spikes)} spike(s) in the data.")
        
        for spike in spikes[:5]:  # Top 5 spikes
            severity = spike.get("severity", "medium")
            severity_color = "🔴" if severity == "high" else "🟠"
            
            with st.expander(f"{severity_color} {spike.get('period', 'Unknown')} - {spike.get('value', 0):,} cases"):
                st.write(f"**Spike Factor:** {spike.get('spike_factor', 0):.2f}x")
                st.write(f"**Moving Average:** {spike.get('moving_avg', 0):.1f}")
                st.write(f"**Severity:** {severity.upper()}")
    
    # Display emerging patterns
    emerging_patterns = trend_data.get("emerging_patterns", [])
    if emerging_patterns:
        st.subheader("🌱 Emerging Patterns")
        st.caption("Sustained increases detected over multiple months.")
        
        for pattern in emerging_patterns[:5]:
            with st.expander(f"Emerging Increase: {pattern.get('start_period')} to {pattern.get('end_period')}"):
                st.write(f"**Duration:** {pattern.get('consecutive_months', 0)} consecutive months")
                st.write(f"**Total Increase:** {pattern.get('total_increase', 0):.1f}%")
    
    # Display statistics
    st.subheader("📊 Trend Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    stability_score = trend_data.get("stability_score", 0)
    trend_direction = trend_data.get("trend_direction", "stable")
    
    col1.metric("Stability Score", f"{stability_score:.2f}", help="0 = unstable, 1 = very stable")
    
    direction_icon = {
        "increasing": "📈",
        "decreasing": "📉",
        "stable": "➡️"
    }.get(trend_direction, "➡️")
    
    col2.metric("Trend Direction", f"{direction_icon} {trend_direction.title()}")
    col3.metric("Spikes Detected", len(spikes))
    col4.metric("Emerging Patterns", len(emerging_patterns))
    
    # Month-over-month changes
    mom_changes = trend_data.get("month_over_month", [])
    if mom_changes and monthly_counts:
        st.subheader("📅 Month-over-Month Changes")
        
        mom_df = pd.DataFrame({
            'month': [m['year_month'] for m in monthly_counts],
            'change_pct': mom_changes[:len(monthly_counts)]
        })
        mom_df = mom_df.dropna()
        
        if not mom_df.empty:
            fig = px.bar(
                mom_df,
                x='month',
                y='change_pct',
                title="Month-over-Month Percentage Change",
                labels={'change_pct': 'Change (%)', 'month': 'Month'}
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

