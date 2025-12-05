"""
Onboarding Wizard - Wave 6
First-time user setup and license activation
"""

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.security.license_manager import LicenseManager

# Page configuration
st.set_page_config(
    page_title="AetherSignal — Welcome",
    page_icon="🚀",
    layout="wide",  # Changed from "centered" for consistent full-width layout
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# Apply theme
apply_theme()

# Top navigation - MUST BE FIRST st.* CALL AFTER apply_theme()
render_top_nav()

# Onboarding wizard
st.markdown("""
<div style="text-align: center; padding: 2rem 1rem;">
    <h1 style="font-size: 3rem; background: linear-gradient(90deg, #3b82f6, #8b5cf6); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               margin-bottom: 1rem;">
        Welcome to AetherSignal
    </h1>
    <p style="font-size: 1.2rem; color: #64748b;">
        Let's get you started in just a few steps
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Step 1: User Information
st.markdown("### Step 1: Your Information")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Your Name", key="onboarding_name", placeholder="John Doe")

with col2:
    organization = st.text_input("Organization", key="onboarding_org", placeholder="Acme Pharmaceuticals")

email = st.text_input("Email", key="onboarding_email", placeholder="john@example.com")

st.markdown("---")

# Step 2: License Activation
st.markdown("### Step 2: Activate Your License")

st.info("💡 If you don't have a license key yet, you can start with a free trial or contact sales.")

license_key = st.text_input(
    "License Key",
    key="onboarding_license",
    type="password",
    placeholder="PRO-XXXX-XXXX-XXXX"
)

st.caption("💡 Demo users can use: DEMO")

# Step 3: Preferences (optional)
st.markdown("---")
st.markdown("### Step 3: Preferences (Optional)")

default_workspace = st.selectbox(
    "Default Workspace",
    ["Signal Explorer", "Social AE Explorer", "Executive Dashboard"],
    key="onboarding_workspace"
)

st.markdown("---")

# Activate button
if st.button("🚀 Activate & Continue", type="primary", use_container_width=True):
    # Validate inputs
    if not name:
        st.error("Please enter your name")
    elif not email:
        st.error("Please enter your email")
    elif not license_key:
        st.warning("⚠️ No license key provided. You'll be using the Starter (free) tier.")
        license_key = "STARTER-FREE"
    
    # Activate license
    try:
        lm = LicenseManager()
        license_info = lm.load_license(license_key)
        
        # Store user info in session
        st.session_state["user_name"] = name
        st.session_state["user_organization"] = organization
        st.session_state["user_email"] = email
        st.session_state["default_workspace"] = default_workspace
        
        st.success(f"✅ Welcome, {name}! License activated for {license_info['tier'].title()} plan.")
        
        # Redirect to home
        st.info("🔄 Redirecting to dashboard...")
        st.switch_page("app.py")
        
    except Exception as e:
        st.error(f"Error activating license: {e}")

# Skip onboarding (for returning users)
st.markdown("---")
if st.button("Skip Setup (Returning User)", use_container_width=True):
    st.switch_page("app.py")

