"""
RPF Charts (CHUNK A - Part 4)
Generates high-quality Plotly charts for RPF visualization.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any


def render_rpf_charts(rpf_result: List[Dict[str, Any]]):
    """
    Render RPF visualization charts.
    
    Args:
        rpf_result: List of RPF result dictionaries
    """
    if not rpf_result:
        return
    
    try:
        df = pd.DataFrame(rpf_result)
        
        if df.empty or "error" in df.columns:
            return
        
        # Chart 1: Top 20 Signals by RPF Score
        st.subheader("📊 Top 20 Signal Priorities (RPF Score)")
        
        top_20 = df.head(20).copy()
        top_20["signal"] = top_20["drug"] + " → " + top_20["reaction"]
        
        fig1 = px.bar(
            top_20,
            x="rpf",
            y="signal",
            orientation="h",
            color="priority",
            color_discrete_map={
                "High": "#EF4444",
                "Medium": "#F59E0B",
                "Low": "#10B981"
            },
            title="Top 20 Signal Priorities (RPF Score)",
            labels={"rpf": "RPF Score", "signal": "Drug → Reaction"}
        )
        fig1.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig1, use_container_width=True)
        
        # Chart 2: Cases vs Seriousness Scatter
        st.subheader("📈 Cases vs Seriousness (Bubble Size = RPF)")
        
        fig2 = px.scatter(
            df,
            x="cases",
            y="serious",
            size="rpf",
            color="priority",
            hover_name=df["drug"] + " → " + df["reaction"],
            hover_data=["rpf", "slope", "disproportionality"],
            color_discrete_map={
                "High": "#EF4444",
                "Medium": "#F59E0B",
                "Low": "#10B981"
            },
            title="Cases vs Seriousness (Bubble Size = RPF Score)",
            labels={
                "cases": "Total Cases",
                "serious": "Serious Cases",
                "rpf": "RPF Score"
            }
        )
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Chart 3: RPF Distribution Histogram
        st.subheader("📉 RPF Score Distribution")
        
        fig3 = px.histogram(
            df,
            x="rpf",
            nbins=30,
            color="priority",
            color_discrete_map={
                "High": "#EF4444",
                "Medium": "#F59E0B",
                "Low": "#10B981"
            },
            title="RPF Score Distribution",
            labels={"rpf": "RPF Score", "count": "Number of Signals"}
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Chart 4: Priority Breakdown Pie Chart
        st.subheader("🥧 Priority Breakdown")
        
        priority_counts = df["priority"].value_counts()
        
        fig4 = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            color=priority_counts.index,
            color_discrete_map={
                "High": "#EF4444",
                "Medium": "#F59E0B",
                "Low": "#10B981"
            },
            title="Signal Priority Distribution"
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering RPF charts: {str(e)}")

