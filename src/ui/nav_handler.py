"""
PHASE 1.2: Centralized Navigation Action Handler
Handles all navigation actions (login, register, profile, logout) from a single location.
"""

import streamlit as st


def handle_nav_actions():
    """
    Centralized navigation action handler.
    Called from render_top_nav() to process nav_action from session state.
    
    This replaces duplicate _handle_nav_actions() functions in individual pages.
    """
    if "nav_action" not in st.session_state:
        return
    
    action = st.session_state.nav_action
    # Clear immediately to prevent loops
    st.session_state.nav_action = None
    
    try:
        if action == "login":
            st.switch_page("pages/Login.py")
        elif action == "register":
            st.switch_page("pages/Register.py")
        elif action == "profile":
            st.switch_page("pages/Profile.py")
        elif action == "logout":
            from src.auth.auth import logout_user
            logout_user()
            st.success("Logged out successfully")
        elif action == "billing":
            st.switch_page("pages/Billing.py")
        elif action == "settings":
            st.switch_page("pages/Settings.py")
        elif action == "api_keys":
            st.switch_page("pages/API_Keys.py")
        elif action == "data_sources":
            st.switch_page("pages/98_Data_Source_Manager.py")
        elif action == "system_diagnostics":
            st.switch_page("pages/System_Diagnostics.py")
    except Exception as e:
        # Log error but don't break page
        st.error(f"Navigation error: {e}")
        # Clear action to prevent infinite loops
        if "nav_action" in st.session_state:
            st.session_state.nav_action = None
