"""
Signal Ranking Table - Phase 3J Step 3
Sortable signal ranking table with quantum scores.
"""

import pandas as pd
import streamlit as st
from typing import Optional


def render_signal_ranking_table(
    signals_df: pd.DataFrame,
    limit: int = 50,
    show_source_breakdown: bool = True
):
    """
    Render signal ranking table.
    
    Args:
        signals_df: DataFrame with ranked signals
        limit: Maximum number of signals to display
        show_source_breakdown: Whether to show source distribution
    """
    if signals_df.empty:
        st.info("No signals available")
        return
    
    st.subheader("📊 Top Ranked Signals (Quantum Engine)")
    st.caption("Signals ranked by Global Risk Index and Quantum Score")
    
    # Prepare display columns
    display_cols = ["drug", "reaction", "quantum_score", "severity_score", "frequency"]
    
    # Add acceleration if available
    if "acceleration" in signals_df.columns:
        display_cols.append("acceleration")
    
    # Add novelty if available
    if "novelty" in signals_df.columns:
        display_cols.append("novelty")
    
    # Filter to available columns
    available_cols = [col for col in display_cols if col in signals_df.columns]
    
    if not available_cols:
        st.warning("No displayable columns found")
        return
    
    # Create display dataframe
    display_df = signals_df[available_cols].head(limit).copy()
    
    # Format columns
    if "quantum_score" in display_df.columns:
        display_df["quantum_score"] = display_df["quantum_score"].round(3)
    
    if "severity_score" in display_df.columns:
        display_df["severity_score"] = display_df["severity_score"].round(2)
    
    if "acceleration" in display_df.columns:
        display_df["acceleration"] = display_df["acceleration"].round(2)
    
    if "novelty" in display_df.columns:
        display_df["novelty"] = display_df["novelty"].round(2)
    
    # Rename columns for display
    column_mapping = {
        "drug": "Drug",
        "reaction": "Reaction",
        "quantum_score": "Quantum Score",
        "severity_score": "Severity",
        "frequency": "Frequency",
        "acceleration": "Acceleration",
        "novelty": "Novelty"
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    # Source breakdown if requested
    if show_source_breakdown and "source" in signals_df.columns:
        st.markdown("#### Source Distribution")
        source_counts = signals_df["source"].value_counts()
        st.bar_chart(source_counts)

