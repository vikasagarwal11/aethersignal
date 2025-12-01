"""
Trends Component - Executive Dashboard
Multi-source trendline visualization
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta


def render_trends():
    """
    Render multi-source AE trend charts.
    """
    st.markdown("### 📈 Adverse Event Trends")
    
    # Try to get real data from backend
    try:
        from executive_dashboard.loaders import load_all_sources
        from executive_dashboard.aggregator import compute_source_trends
        
        df = load_all_sources()
        trends = compute_source_trends(df)
        
        # Convert to DataFrame for plotting
        trend_data = []
        for source, data in trends.items():
            for date, count in data.items():
                trend_data.append({
                    "date": pd.to_datetime(date),
                    "count": count,
                    "source": source
                })
        
        if trend_data:
            df_trends = pd.DataFrame(trend_data)
        else:
            raise ValueError("No trend data")
            
    except Exception:
        # Fallback to mock data
        dates = pd.date_range(start="2024-01-01", periods=180, freq="D")
        df_trends = pd.DataFrame({
            "date": dates,
            "faers": (pd.Series(range(180)) * 1.5 + 100).values,
            "social": (pd.Series(range(180)) * 2.2 + 50).values,
            "literature": (pd.Series(range(180)) * 0.9 + 20).values,
        })
        
        # Reshape for Plotly
        df_trends = df_trends.melt(
            id_vars=["date"],
            value_vars=["faers", "social", "literature"],
            var_name="source",
            value_name="count"
        )
    
    # Create line chart
    from src.ui.layout.theme import get_theme_colors
    colors = get_theme_colors()
    color_map = {
        "faers": colors["primary"],
        "social": "#e11d48",
        "literature": colors["success"],
        "FAERS": colors["primary"],
        "Social": "#e11d48",
        "Literature": colors["success"]
    }
    
    fig = px.line(
        df_trends,
        x="date",
        y="count",
        color="source",
        labels={"value": "Count", "date": "Date", "source": "Source"},
        color_discrete_map=color_map,
        markers=True
    )
    
    fig.update_layout(
        height=350,
        legend_title_text="Source",
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="AE Count"
    )
    
    st.plotly_chart(fig, use_container_width=True)

