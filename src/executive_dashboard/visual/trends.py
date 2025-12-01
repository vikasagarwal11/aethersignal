"""
Multi-Source Trend Charts - Phase 3J Step 3
Trendline visualizations for all sources.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, Optional
from datetime import datetime, timedelta


def render_multi_source_trends(
    trend_df: pd.DataFrame,
    source_trends: Optional[pd.DataFrame] = None,
    forecast_days: int = 30
):
    """
    Render multi-source trend charts.
    
    Args:
        trend_df: Combined trend DataFrame
        source_trends: Optional DataFrame with trends by source
        forecast_days: Days to forecast ahead
    """
    if trend_df.empty:
        st.info("No trend data available")
        return
    
    # Main combined trend
    fig = go.Figure()
    
    # Combined trendline
    fig.add_trace(go.Scatter(
        x=trend_df["period_str"],
        y=trend_df["count"],
        mode="lines+markers",
        name="All Sources",
        line=dict(width=3, color="#2563eb"),
        marker=dict(size=6)
    ))
    
    # Add source-specific trends if available
    if source_trends is not None and not source_trends.empty:
        sources = source_trends["source"].unique()
        colors = {"FAERS": "#dc2626", "SOCIAL": "#16a34a", "LITERATURE": "#ea580c", "CLINICAL_TRIALS": "#7c3aed"}
        
        for source in sources:
            source_data = source_trends[source_trends["source"] == source]
            if not source_data.empty:
                fig.add_trace(go.Scatter(
                    x=source_data["period_str"],
                    y=source_data["count"],
                    name=source,
                    mode="lines",
                    line=dict(width=2, color=colors.get(source, "#6b7280")),
                    opacity=0.7
                ))
    
    # Add moving average
    if len(trend_df) >= 3:
        trend_df["ma"] = trend_df["count"].rolling(window=3, center=True).mean()
        fig.add_trace(go.Scatter(
            x=trend_df["period_str"],
            y=trend_df["ma"],
            name="Moving Average (3-period)",
            mode="lines",
            line=dict(width=2, color="#f59e0b", dash="dash"),
            opacity=0.6
        ))
    
    fig.update_layout(
        title="Adverse Event Trends (Multi-Source)",
        xaxis_title="Period",
        yaxis_title="Event Count",
        height=400,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend summary metrics
    if not trend_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_count = trend_df["count"].mean()
            st.metric("Avg Monthly", f"{avg_count:.0f}")
        
        with col2:
            max_count = trend_df["count"].max()
            st.metric("Peak", f"{max_count:.0f}")
        
        with col3:
            recent_trend = trend_df.tail(3)["count"].mean() if len(trend_df) >= 3 else 0
            st.metric("Recent Avg", f"{recent_trend:.0f}")
        
        with col4:
            if len(trend_df) >= 2:
                latest = trend_df["count"].iloc[-1]
                previous = trend_df["count"].iloc[-2]
                change = ((latest - previous) / previous * 100) if previous > 0 else 0
                st.metric("MoM Change", f"{change:+.1f}%")

