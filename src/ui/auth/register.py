"""
Registration page UI component for AetherSignal.
"""

import streamlit as st
from src.auth.auth import register_user, is_authenticated


def render_register_page() -> None:
    """Render registration page."""
    
    st.markdown("## 📝 Create Your AetherSignal Account")
    st.caption("Join AetherSignal to start analyzing pharmacovigilance data")
    
    # If already authenticated, redirect
    if is_authenticated():
        st.success("✅ You are already logged in!")
        if st.button("Go to Dashboard", use_container_width=True):
            st.switch_page("pages/1_Quantum_PV_Explorer.py")
        return
    
    # Clear any previous state
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Registration form
    with st.form("register_form"):
        st.markdown("### Account Information")
        
        email = st.text_input(
            "Email *",
            placeholder="your.email@company.com",
            key="register_email",
            help="We'll send a verification email to this address"
        )
        
        password = st.text_input(
            "Password *",
            type="password",
            placeholder="Minimum 8 characters",
            key="register_password",
            help="Password must be at least 8 characters long"
        )
        
        password_confirm = st.text_input(
            "Confirm Password *",
            type="password",
            placeholder="Re-enter your password",
            key="register_password_confirm"
        )
        
        st.markdown("### Profile Information")
        
        full_name = st.text_input(
            "Full Name *",
            placeholder="John Doe",
            key="register_full_name"
        )
        
        organization = st.text_input(
            "Company/Organization *",
            placeholder="Your Company Name",
            key="register_organization",
            help="This will be used to isolate your data from other companies"
        )
        
        role = st.selectbox(
            "Role *",
            options=["scientist", "viewer", "admin"],
            index=0,
            key="register_role",
            help="Scientist: Full access | Viewer: Read-only | Admin: Full access + user management"
        )
        
        st.markdown("### Terms & Conditions")
        terms_accepted = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy *",
            key="register_terms",
            help="You must accept the terms to create an account"
        )
        
        # Prevent duplicate submissions
        submit_key = "register_form_submit"
        if submit_key not in st.session_state:
            st.session_state[submit_key] = False
        
        if st.form_submit_button("Create Account", type="primary", use_container_width=True):
            # Check if already processing
            if st.session_state[submit_key]:
                st.warning("⏳ Registration in progress. Please wait...")
                return
            
            # Set processing flag
            st.session_state[submit_key] = True
            
            try:
                # Validation
                errors = []
                
                if not email or "@" not in email:
                    errors.append("Please enter a valid email address.")
                
                if not password or len(password) < 8:
                    errors.append("Password must be at least 8 characters long.")
                
                if password != password_confirm:
                    errors.append("Passwords do not match.")
                
                if not full_name:
                    errors.append("Please enter your full name.")
                
                if not organization:
                    errors.append("Please enter your company/organization name.")
                
                if not terms_accepted:
                    errors.append("You must accept the Terms of Service to create an account.")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Register user
                    with st.spinner("Creating your account..."):
                        result = register_user(
                            email=email,
                            password=password,
                            full_name=full_name,
                            organization=organization,
                            role=role
                        )
                    
                    if result.get("success"):
                        st.success(result.get("message", "Account created successfully!"))
                        st.info("📧 Please check your email to verify your account. You can login after verification.")
                        st.session_state.show_register = False
                        st.session_state.show_login = True
                        st.session_state[submit_key] = False
                        st.rerun()
                    else:
                        error_msg = result.get("error", "Registration failed. Please try again.")
                        st.error(error_msg)
                        
                        # If rate limited, show countdown
                        if result.get("rate_limited"):
                            wait_seconds = result.get("wait_seconds", 60)
                            st.warning(f"⏱️ Please wait {wait_seconds} seconds before trying again.")
                            
            finally:
                # Reset processing flag after a delay
                import time
                time.sleep(0.5)
                st.session_state[submit_key] = False
    
    # Login link
    st.markdown("---")
    st.markdown("Already have an account?")
    if st.button("🔐 Login", use_container_width=True):
        st.session_state.show_register = False
        st.session_state.show_login = True
        st.rerun()

