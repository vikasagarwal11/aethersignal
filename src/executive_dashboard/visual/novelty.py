"""
Novelty Detector Panel - Phase 3J Step 3
Detects and displays novel signals (social/literature but not FAERS).
"""

import pandas as pd
import streamlit as st
from typing import Optional
import plotly.express as px


def render_novelty_panel(
    novelty_df: pd.DataFrame,
    show_venn: bool = True
):
    """
    Render novelty detection panel.
    
    Args:
        novelty_df: DataFrame with novel signals
        show_venn: Whether to show Venn diagram visualization
    """
    st.subheader("🔍 Novel Signals Detection")
    st.caption("Reactions appearing in Social/Literature but not yet in FAERS")
    
    if novelty_df.empty:
        st.success("✅ No novel signals detected. All reactions are present in FAERS.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Novel Signals", len(novelty_df))
    
    with col2:
        avg_quantum = novelty_df["quantum_score"].mean() if "quantum_score" in novelty_df.columns else 0
        st.metric("Avg Quantum Score", f"{avg_quantum:.2f}")
    
    with col3:
        high_severity = novelty_df[novelty_df["severity_score"] >= 0.7].shape[0] if "severity_score" in novelty_df.columns else 0
        st.metric("High Severity", high_severity)
    
    # Display table
    display_cols = ["drug", "reaction", "quantum_score", "severity_score", "count"]
    available_cols = [col for col in display_cols if col in novelty_df.columns]
    
    if available_cols:
        display_df = novelty_df[available_cols].copy()
        
        # Format scores
        if "quantum_score" in display_df.columns:
            display_df["quantum_score"] = display_df["quantum_score"].round(3)
        if "severity_score" in display_df.columns:
            display_df["severity_score"] = display_df["severity_score"].round(2)
        
        # Rename for display
        display_df = display_df.rename(columns={
            "drug": "Drug",
            "reaction": "Reaction",
            "quantum_score": "Quantum Score",
            "severity_score": "Severity",
            "count": "Cases"
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=300,
            hide_index=True
        )
    
    # Visualization
    if show_venn and len(novelty_df) > 0:
        st.markdown("#### Novel Signals by Drug")
        
        if "drug" in novelty_df.columns:
            drug_counts = novelty_df["drug"].value_counts().head(10)
            
            fig = px.bar(
                x=drug_counts.index,
                y=drug_counts.values,
                labels={"x": "Drug", "y": "Novel Signals"},
                title="Top Drugs with Novel Signals"
            )
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

