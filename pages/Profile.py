"""
User profile page for AetherSignal.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.ui.auth.profile import render_profile_page
from src.auth.auth import is_authenticated

st.set_page_config(
    page_title="AetherSignal – Profile",
    page_icon="👤",
    layout="wide",  # Changed from "centered" for consistent full-width layout
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

apply_theme()
render_top_nav()  # MUST BE FIRST st.* CALL AFTER apply_theme()
# PHASE 1.2: Navigation action handling is now centralized in nav_handler.py
# No need for nav_action handling here - it's called from render_top_nav()

# Add spacing for top nav
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

if not is_authenticated():
    st.warning("⚠️ Please login to view your profile.")
    if st.button("Go to Login", use_container_width=True):
        st.switch_page("pages/Login.py")
else:
    render_profile_page()

