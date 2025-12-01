"""
Executive Dashboard - Main Entry Point
Enterprise-grade executive safety intelligence dashboard
"""

import streamlit as st
from src.ui.layout.base_layout import render_base_layout
from src.ui.layout.state import GlobalState
from .kpi_tiles import render_kpi_tiles
from .trends import render_trends
from .signal_tables import render_top_signals_table
from .heatmaps import render_severity_heatmap
from .novelty import render_novelty_panel
from .source_mix import render_source_mix
from .risk_matrix import render_risk_matrix
from .summaries import render_executive_summary


def render_executive_dashboard():
    """
    Render the complete executive dashboard.
    """
    def page_content():
        # Page header
        st.markdown("## 🌍 Executive Drug Safety Dashboard")
        st.caption("Multi-source safety intelligence for executive decision-making")
        st.markdown("---")
        
        # KPI Tiles
        render_kpi_tiles()
        
        st.markdown("---")
        
        # Trends Section
        render_trends()
        
        st.markdown("---")
        
        # Top Signals Table
        render_top_signals_table()
        
        st.markdown("---")
        
        # Two-column layout for heatmaps
        col1, col2 = st.columns(2)
        
        with col1:
            render_severity_heatmap()
        
        with col2:
            render_source_mix()
        
        st.markdown("---")
        
        # Novelty Panel
        render_novelty_panel()
        
        st.markdown("---")
        
        # Risk Matrix
        render_risk_matrix()
        
        st.markdown("---")
        
        # Executive Summary
        render_executive_summary()
    
    # Render with base layout
    render_base_layout(page_content)

