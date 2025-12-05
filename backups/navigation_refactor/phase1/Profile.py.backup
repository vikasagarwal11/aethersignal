"""
User profile page for AetherSignal.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Restore authentication session first, before anything else
try:
    from src.auth.auth import restore_session
    restore_session()
except Exception:
    pass

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.ui.auth.profile import render_profile_page
from src.auth.auth import is_authenticated

st.set_page_config(
    page_title="AetherSignal – Profile",
    page_icon="👤",
    layout="centered",
    initial_sidebar_state="expanded",
)

apply_theme()
render_top_nav()

# Handle nav actions from top nav
nav_action = st.session_state.get("nav_action")
if nav_action == "login":
    st.switch_page("pages/Login.py")
elif nav_action == "register":
    st.switch_page("pages/Register.py")
elif nav_action == "profile":
    pass  # Already on profile page
elif nav_action == "logout":
    try:
        from src.auth.auth import logout_user
        logout_user()
        st.rerun()
    except Exception:
        pass
if "nav_action" in st.session_state:
    st.session_state.nav_action = None

# Add spacing for top nav
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

if not is_authenticated():
    st.warning("⚠️ Please login to view your profile.")
    if st.button("Go to Login", use_container_width=True):
        st.switch_page("pages/Login.py")
else:
    render_profile_page()

