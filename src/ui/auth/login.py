"""
Login page UI component for AetherSignal.
"""

import streamlit as st
from src.auth.auth import login_user, reset_password, is_authenticated


def render_login_page() -> None:
    """Render login page."""
    
    st.markdown("## 🔐 Login to AetherSignal")
    st.caption("Enter your credentials to access your pharmacovigilance data")
    
    # If already authenticated, redirect
    if is_authenticated():
        st.success("✅ You are already logged in!")
        if st.button("Go to Dashboard", use_container_width=True):
            st.switch_page("pages/1_Quantum_PV_Explorer.py")
        return
    
    # Clear any previous errors
    if 'show_password_reset' not in st.session_state:
        st.session_state.show_password_reset = False
    
    # Login form
    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="your.email@company.com",
            key="login_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        col1, col2 = st.columns([2, 1])
        with col1:
            remember_me = st.checkbox("Remember me", key="login_remember")
        with col2:
            if st.form_submit_button("Login", type="primary", use_container_width=True):
                if email and password:
                    result = login_user(email, password)
                    if result.get("success"):
                        st.success(result.get("message", "Login successful!"))
                        st.rerun()
                    else:
                        st.error(result.get("error", "Login failed. Please try again."))
                else:
                    st.warning("Please enter both email and password.")
    
    # Forgot password link
    st.markdown("---")
    if st.button("🔑 Forgot Password?", use_container_width=True):
        st.session_state.show_password_reset = True
    
    if st.session_state.get("show_password_reset", False):
        with st.form("password_reset_form"):
            reset_email = st.text_input(
                "Enter your email",
                placeholder="your.email@company.com",
                key="reset_email"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.form_submit_button("Send Reset Link", use_container_width=True):
                    if reset_email:
                        result = reset_password(reset_email)
                        if result.get("success"):
                            st.success(result.get("message", "Password reset email sent!"))
                            st.session_state.show_password_reset = False
                        else:
                            st.error(result.get("error", "Failed to send reset email."))
                    else:
                        st.warning("Please enter your email address.")
            
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_password_reset = False
                    st.rerun()
    
    # Register link
    st.markdown("---")
    st.markdown("Don't have an account?")
    if st.button("📝 Create Account", use_container_width=True):
        st.session_state.show_register = True
        st.rerun()

