"""
RPF Panel (CHUNK A - Part 6)
Complete RPF (Risk Prioritization Framework) panel with weights, computation, tables, and charts.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Optional, List, Any

from .rpf_weights_panel import render_rpf_weights_panel
from .rpf_table import render_rpf_table
from .rpf_charts import render_rpf_charts
from src.ai.hybrid_router import run_hybrid_rpf


def render_rpf_panel(df: pd.DataFrame):
    """
    Render complete RPF (Risk Prioritization Framework) panel.
    
    Includes:
    - Weight configuration
    - Processing mode selection
    - RPF computation
    - Results table
    - Visualization charts
    
    Args:
        df: Safety data DataFrame
    """
    st.header("📊 Risk Prioritization Framework (RPF)")
    st.caption("Configurable, hybrid, and supports full offline mode. RPF scores help prioritize signals for review.")
    
    if df is None or df.empty:
        st.warning("⚠️ Please load data first to compute RPF scores.")
        return
    
    # Weight configuration
    st.markdown("---")
    weights = render_rpf_weights_panel()
    
    # Processing mode selection
    st.markdown("---")
    st.subheader("⚙️ Processing Mode")
    
    mode = st.radio(
        "Select Processing Mode:",
        ["Auto", "Local", "Server"],
        index=0,
        horizontal=True,
        help="Auto: Intelligent selection based on dataset size and browser capabilities. Local: Fast browser-side computation. Server: Full server-side analysis."
    )
    
    # Compute button
    col1, col2 = st.columns([1, 4])
    with col1:
        compute_button = st.button("⚡ Compute RPF", type="primary", use_container_width=True)
    
    with col2:
        if "rpf_data" in st.session_state:
            st.success(f"✅ RPF computed: {len(st.session_state.rpf_data)} signals ranked")
    
    # Compute RPF
    if compute_button:
        with st.spinner("Computing RPF scores..."):
            try:
                rpf_results = run_hybrid_rpf(df, weights, mode.lower())
                st.session_state.rpf_data = rpf_results
                st.session_state.rpf_weights_used = weights
                st.session_state.rpf_mode_used = mode.lower()
                st.success(f"✅ RPF computation complete: {len(rpf_results)} signals ranked")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error computing RPF: {str(e)}")
                st.session_state.rpf_data = None
    
    # Display results if available
    if "rpf_data" in st.session_state and st.session_state.rpf_data:
        st.markdown("---")
        
        # Mode indicator
        mode_used = st.session_state.get("rpf_mode_used", "auto")
        mode_colors = {
            "auto": "blue",
            "local": "green",
            "server": "orange"
        }
        mode_color = mode_colors.get(mode_used, "gray")
        
        st.markdown(
            f"""
            <div style="padding:8px 12px; border-radius:6px; background-color:{mode_color}; color:white; 
                display:inline-block; margin-bottom:12px;">
                ⚡ Processing Mode: <b>{mode_used.upper()}</b>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Results tabs
        tab1, tab2 = st.tabs(["📋 Results Table", "📊 Charts"])
        
        with tab1:
            render_rpf_table(st.session_state.rpf_data)
        
        with tab2:
            render_rpf_charts(st.session_state.rpf_data)
        
        # Export options
        st.markdown("---")
        st.subheader("💾 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download as CSV"):
                rpf_df = pd.DataFrame(st.session_state.rpf_data)
                csv = rpf_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"rpf_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📄 Generate RPF Report"):
                st.info("RPF report generation coming soon...")

