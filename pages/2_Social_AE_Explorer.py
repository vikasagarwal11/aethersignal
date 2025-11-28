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
# Sidebar actions listener helpers
# -------------------------------------------------------------------
def _handle_nav_actions():
    nav_action = st.session_state.get("nav_action")
    if nav_action == "login":
        st.switch_page("pages/Login.py")
    elif nav_action == "register":
        st.switch_page("pages/Register.py")
    elif nav_action == "profile":
        st.switch_page("pages/Profile.py")
    elif nav_action == "logout":
        try:
            from src.auth.auth import logout_user
            logout_user()
        except Exception:
            pass
        st.session_state.nav_action = None
        st.rerun()
    if "nav_action" in st.session_state:
        st.session_state.nav_action = None

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

# Check authentication (optional for Social AE - can be public)
# Uncomment below if you want to require authentication for Social AE
# if not is_authenticated():
#     st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
#     st.warning("⚠️ Please login to access the Social AE Explorer.")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("🔐 Login", use_container_width=True):
#             st.switch_page("pages/Login.py")
#     with col2:
#         if st.button("📝 Register", use_container_width=True):
#             st.switch_page("pages/Register.py")
#     st.stop()

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
render_header(page_type="social")
render_banner()

with st.sidebar:
    from src.ui import sidebar
    sidebar.render_sidebar()
    _handle_nav_actions()


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
