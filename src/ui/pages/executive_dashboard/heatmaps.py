"""
Heatmap Components - Executive Dashboard
Severity and source distribution visualizations
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def render_severity_heatmap():
    """
    Render severity heatmap visualization.
    """
    st.markdown("#### Severity Heatmap")
    
    # Try to get real data
    try:
        from executive_dashboard.loaders import load_all_sources
        
        df = load_all_sources()
        
        if df is not None and not df.empty and "reaction" in df.columns and "severity" in df.columns:
            severity_data = df.groupby("reaction")["severity"].mean().reset_index()
            severity_data = severity_data.sort_values("severity", ascending=False).head(10)
        else:
            raise ValueError("No severity data")
            
    except Exception:
        # Fallback to mock data
        severity_data = pd.DataFrame({
            "reaction": ["Nausea", "Vomiting", "Headache", "Hair Loss", "Fatigue"],
            "severity": [0.6, 0.7, 0.4, 0.2, 0.3]
        })
    
    # Create heatmap
    fig = px.bar(
        severity_data,
        x="severity",
        y="reaction",
        orientation="h",
        color="severity",
        color_continuous_scale="Reds",
        labels={"severity": "Severity Score", "reaction": "Reaction"},
        height=300
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_range=[0, 1],
        yaxis={"categoryorder": "total ascending"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

