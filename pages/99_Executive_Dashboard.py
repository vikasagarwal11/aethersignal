"""
Executive Drug Safety Dashboard - Phase 3J
Main Streamlit page for executive-level safety intelligence.
"""

import streamlit as st

# MUST BE IN EVERY PAGE — Streamlit does NOT inherit config
st.set_page_config(
    page_title="AetherSignal — Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

from src.styles import apply_theme
apply_theme()

from src.ui.top_nav import render_top_nav
render_top_nav()  # MUST BE FIRST st.* CALL AFTER apply_theme()

from src.executive_dashboard.dashboard import render_executive_dashboard

# Render the dashboard
render_executive_dashboard()

