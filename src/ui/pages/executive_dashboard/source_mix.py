"""
Source Mix Component - Executive Dashboard
Source distribution visualization
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def render_source_mix():
    """
    Render source distribution pie chart.
    """
    st.markdown("#### Source Distribution")
    
    # Try to get real data
    try:
        from executive_dashboard.loaders import load_all_sources
        
        df = load_all_sources()
        
        if df is not None and not df.empty and "source" in df.columns:
            source_counts = df["source"].value_counts()
            source_data = pd.DataFrame({
                "source": source_counts.index,
                "count": source_counts.values
            })
        else:
            raise ValueError("No source data")
            
    except Exception:
        # Fallback to mock data
        source_data = pd.DataFrame({
            "source": ["FAERS", "Social", "Literature"],
            "count": [68, 22, 10]
        })
    
    # Create pie chart
    colors = get_theme_colors()
    color_map = {
        "FAERS": colors["primary"],
        "Social": "#e11d48",
        "Literature": colors["success"],
        "faers": colors["primary"],
        "social": "#e11d48",
        "literature": colors["success"]
    }
    
    fig = px.pie(
        source_data,
        names="source",
        values="count",
        color="source",
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_layout(
        height=300,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)

