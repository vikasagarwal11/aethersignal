"""
Login page for AetherSignal.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.ui.auth.login import render_login_page

st.set_page_config(
    page_title="AetherSignal – Login",
    page_icon="🔐",
    layout="wide",  # Changed from "centered" for consistent full-width layout
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

apply_theme()
render_top_nav()  # MUST BE FIRST st.* CALL AFTER apply_theme()
# PHASE 1.2: Navigation action handling is now centralized in nav_handler.py
# No need for nav_action handling here - it's called from render_top_nav()

# Check if already authenticated - redirect to dashboard
from src.auth.auth import is_authenticated
if is_authenticated():
    st.switch_page("pages/1_Quantum_PV_Explorer.py")

# Add spacing for top nav
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

render_login_page()

