"""
Login page for AetherSignal.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.ui.auth.login import render_login_page

st.set_page_config(
    page_title="AetherSignal – Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav()

# Handle nav actions from top nav
nav_action = st.session_state.get("nav_action")
if nav_action == "login":
    pass  # Already on login page
elif nav_action == "register":
    st.switch_page("pages/Register.py")
elif nav_action == "profile":
    st.switch_page("pages/Profile.py")
elif nav_action == "logout":
    try:
        from src.auth.auth import logout_user
        logout_user()
        st.rerun()
    except Exception:
        pass
if "nav_action" in st.session_state:
    st.session_state.nav_action = None

# Check if already authenticated - redirect to dashboard
from src.auth.auth import is_authenticated
if is_authenticated():
    st.switch_page("pages/1_Quantum_PV_Explorer.py")

# Add spacing for top nav
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

render_login_page()

