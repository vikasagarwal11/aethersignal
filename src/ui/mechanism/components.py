"""
Shared UI blocks for mechanism views
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any


def kpi_tile(label: str, value: str, color: str = "#2563eb"):
    """
    Render a KPI tile.
    
    Args:
        label: KPI label
        value: KPI value
        color: Color theme
    """
    st.markdown(f"""
        <div style="
            padding: 14px;
            border-radius: 10px;
            background: {color}20;
            border: 1px solid {color}30;
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: {color};">{label}</h4>
            <h2 style="margin: 0; font-weight: 700;">{value}</h2>
        </div>
    """, unsafe_allow_html=True)


def similarity_heatmap(similarities: List[Dict[str, Any]]):
    """
    Render similarity heatmap.
    
    Args:
        similarities: List of similarity dictionaries
    """
    if not similarities:
        st.info("No embedding similarities available.")
        return
    
    try:
        # Create DataFrame
        df = pd.DataFrame(similarities)
        
        # Prepare data for heatmap
        if "distance" in df.columns:
            data = df[["distance"]].T
        elif "similarity" in df.columns:
            data = df[["similarity"]].T
        else:
            # Use first numeric column
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                data = df[[numeric_cols[0]]].T
            else:
                st.warning("No numeric similarity data found.")
                return
        
        fig = px.imshow(
            data,
            labels=dict(x="Index", y="Metric", color="Score"),
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering similarity heatmap: {e}")


def pathway_list(pathways: List[Dict[str, Any]]):
    """
    Render list of pathways.
    
    Args:
        pathways: List of pathway dictionaries
    """
    if not pathways:
        st.warning("No related pathways found.")
        return
    
    for idx, p in enumerate(pathways):
        pathway_text = p.get("text", p.get("name", f"Pathway {idx}"))
        distance = p.get("distance", 0.0)
        
        st.markdown(f"""
        <div style="
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #22c55e;
            background: #f0fdf4;
        ">
            <strong>Pathway:</strong><br>
            {pathway_text}
            <br><small style="color: #6b7280;">Distance: {round(distance, 4)}</small>
        </div>
        """, unsafe_allow_html=True)


def mechanism_card(mechanism: Dict[str, Any]):
    """
    Render a mechanism card.
    
    Args:
        mechanism: Mechanism dictionary
    """
    title = mechanism.get("title", mechanism.get("name", "Mechanism"))
    description = mechanism.get("description", mechanism.get("text", ""))
    confidence = mechanism.get("confidence", mechanism.get("score", 0.0))
    
    st.markdown(f"""
    <div style="
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 8px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    ">
        <h4 style="margin: 0 0 8px 0;">{title}</h4>
        <p style="margin: 0 0 8px 0; color: #64748b;">{description[:200]}...</p>
        <small style="color: #94a3b8;">Confidence: {round(confidence, 3)}</small>
    </div>
    """, unsafe_allow_html=True)

