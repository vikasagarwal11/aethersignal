"""
RPF Table Renderer (CHUNK A - Part 3)
Displays RPF results in a formatted, interactive table.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_rpf_table(rpf_result: List[Dict[str, Any]]):
    """
    Render RPF results in a formatted table.
    
    Args:
        rpf_result: List of RPF result dictionaries
    """
    if not rpf_result:
        st.info("No RPF results available.")
        return
    
    try:
        df = pd.DataFrame(rpf_result)
        
        if df.empty:
            st.info("No RPF results to display.")
            return
        
        # Remove error entries
        if "error" in df.columns:
            df = df[df["error"].isna()]
        
        if df.empty:
            st.warning("No valid RPF results after filtering.")
            return
        
        # Format columns
        display_df = df.copy()
        
        # Highlight high-priority signals
        def highlight_priority(row):
            if row["priority"] == "High":
                return ['background-color: #FEE2E2'] * len(row)
            elif row["priority"] == "Medium":
                return ['background-color: #FEF3C7'] * len(row)
            else:
                return [''] * len(row)
        
        # Display table with styling
        st.dataframe(
            display_df.style.apply(highlight_priority, axis=1),
            use_container_width=True,
            height=400
        )
        
        # Summary statistics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Signals", len(df))
        with col2:
            high_count = len(df[df["priority"] == "High"])
            st.metric("High Priority", high_count)
        with col3:
            avg_rpf = df["rpf"].mean()
            st.metric("Avg RPF Score", f"{avg_rpf:.1f}")
        with col4:
            max_rpf = df["rpf"].max()
            st.metric("Max RPF Score", f"{max_rpf:.1f}")
        
    except Exception as e:
        st.error(f"Error rendering RPF table: {str(e)}")

