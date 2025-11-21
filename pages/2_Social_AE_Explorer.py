"""
Social AE Explorer Page
Full-page module for exploring social media adverse events.
"""

import streamlit as st

from src.styles import apply_theme
from src.app_helpers import initialize_session
from src.ui.top_nav import render_top_nav
from src.ui.header import render_header, render_banner
from src.social_ae import render_social_ae_module


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Social AE Explorer – AetherSignal",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",  # Changed to expanded so sidebar toggle is always visible
)


# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()


# -------------------------------------------------------------------
# Initialize session state
# -------------------------------------------------------------------
initialize_session()


# -------------------------------------------------------------------
# TOP NAVIGATION
# -------------------------------------------------------------------
render_top_nav()

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
render_header(page_type="social")
render_banner()


# -------------------------------------------------------------------
# SOCIAL AE EXPLORER MODULE
# -------------------------------------------------------------------
st.markdown("## 🌐 Social AE Explorer")
st.caption(
    "Real-time patient-reported adverse events from Reddit, X, and patient forums. "
    "⚠️ Exploratory only - not validated for regulatory use."
)

# Render the full Social AE module (no expander wrapper)
render_social_ae_module()

