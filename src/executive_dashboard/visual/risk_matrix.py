"""
Severity Matrix Heatmap - Phase 3J Step 3
Severity vs Reaction heatmap visualization.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from typing import Optional
import numpy as np


def render_severity_matrix(
    df: pd.DataFrame,
    drug: Optional[str] = None
):
    """
    Render severity matrix heatmap.
    
    Args:
        df: Unified AE DataFrame
        drug: Optional drug filter
    """
    if df.empty:
        st.info("No data available for severity matrix")
        return
    
    if "severity_score" not in df.columns:
        st.info("Severity engine disabled or no severity data available")
        return
    
    # Filter by drug if specified
    if drug:
        df = df[df["drug"].str.contains(drug, case=False, na=False)]
    
    if df.empty:
        st.info("No data for selected drug")
        return
    
    # Create severity bins
    df["severity_bin"] = pd.cut(
        df["severity_score"],
        bins=[0, 0.3, 0.6, 0.8, 1.0],
        labels=["Low", "Moderate", "High", "Severe"]
    )
    
    # Pivot table: Reaction vs Severity
    pivot = df.pivot_table(
        index="reaction",
        columns="severity_bin",
        values="severity_score",
        aggfunc="count",
        fill_value=0
    )
    
    if pivot.empty:
        st.info("No data available for pivot")
        return
    
    # Sort by total count
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).head(20)  # Top 20 reactions
    pivot = pivot.drop(columns=["total"])
    
    # Create heatmap
    fig = px.imshow(
        pivot,
        labels=dict(x="Severity Level", y="Reaction", color="Case Count"),
        color_continuous_scale="Reds",
        aspect="auto",
        title="Severity Matrix: Reaction × Severity Distribution"
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Severity Level",
        yaxis_title="Reaction"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        low_count = df[df["severity_score"] < 0.3].shape[0]
        st.metric("Low Severity", f"{low_count:,}")
    
    with col2:
        moderate_count = df[(df["severity_score"] >= 0.3) & (df["severity_score"] < 0.6)].shape[0]
        st.metric("Moderate Severity", f"{moderate_count:,}")
    
    with col3:
        high_severe_count = df[df["severity_score"] >= 0.6].shape[0]
        st.metric("High/Severe", f"{high_severe_count:,}")

