"""
Risk Matrix Component - Executive Dashboard
Risk visualization scatter plot
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def render_risk_matrix():
    """
    Render risk matrix scatter plot.
    """
    st.markdown("### ⚠️ Risk Matrix")
    
    # Try to get real data
    try:
        from executive_dashboard.loaders import load_all_sources
        
        df = load_all_sources()
        
        if df is not None and not df.empty:
            if "reaction" in df.columns and "severity" in df.columns:
                risk_data = df.groupby("reaction").agg({
                    "severity": "mean",
                    "drug": "count"  # Use as frequency proxy
                }).reset_index()
                risk_data.columns = ["reaction", "severity", "frequency"]
                risk_data = risk_data.sort_values("frequency", ascending=False).head(15)
            else:
                raise ValueError("Missing columns")
        else:
            raise ValueError("No data")
            
    except Exception:
        # Fallback to mock data
        risk_data = pd.DataFrame({
            "reaction": ["Nausea", "Vomiting", "Headache", "Hair Loss", "Fatigue"],
            "severity": [0.6, 0.7, 0.4, 0.2, 0.3],
            "frequency": [420, 310, 280, 112, 95]
        })
    
    # Create scatter plot
    fig = px.scatter(
        risk_data,
        x="frequency",
        y="severity",
        text="reaction",
        size="frequency",
        color="severity",
        color_continuous_scale="Reds",
        labels={
            "frequency": "Frequency (Count)",
            "severity": "Severity Score",
            "reaction": "Reaction"
        },
        hover_data=["reaction"]
    )
    
    fig.update_traces(
        textposition="top center",
        textfont_size=10
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Frequency",
        yaxis_title="Severity Score",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

