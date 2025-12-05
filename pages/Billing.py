"""
Billing & Subscription Page - Wave 6
Stripe-ready billing interface
Protected: org_admin + super_admin only
"""

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.auth.auth import is_authenticated
from src.ui.top_nav import render_top_nav
from src.auth.admin_helpers import require_admin
from src.config.pricing_tiers import PRICING_TIERS, get_tier_info
from src.security.license_manager import LicenseManager
from src.utils.config_loader import get_config_value

# Page configuration
st.set_page_config(
    page_title="AetherSignal — Billing & Subscription",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# Apply theme
apply_theme()

# Top navigation - MUST BE FIRST st.* CALL AFTER apply_theme()
render_top_nav()

# Guard: org admin + super_admin only
try:
    require_admin()
except PermissionError as e:
    st.title("💳 Billing & Subscription")
    st.error("🔒 Access Denied")
    st.info(
        "Billing is only available to organization administrators or platform owners. "
        "If you believe you should have access, please contact your admin or AetherSignal support."
    )
    st.stop()

# Check if pricing is enabled
pricing_enabled = get_config_value("enable_pricing", False)

# Page header
st.markdown("# 💳 Billing & Subscription")

if not pricing_enabled:
    st.info("🎉 **Pricing is currently disabled.** All features are available for free!")
    st.markdown("---")
    st.markdown("### ✅ All Features Unlocked")
    st.markdown("""
    Since pricing is disabled, you have access to:
    - ✅ All data sources (FAERS, Social, Literature)
    - ✅ Executive Dashboard
    - ✅ Safety Copilot
    - ✅ Mechanism AI
    - ✅ PSUR/DSUR Generator
    - ✅ Workflow Automation
    - ✅ Unlimited API calls
    - ✅ All premium features
    
    Enjoy! 🚀
    """)
    st.stop()

st.caption("Choose a plan that fits your needs")

# Get current tier
lm = LicenseManager()
current_tier = lm.get_tier()
current_info = lm.get_license_info()

if current_info:
    st.info(f"✅ **Current Plan:** {current_info.get('tier', 'starter').title()}")

st.markdown("---")

# Pricing cards
col1, col2, col3 = st.columns(3)

tiers = ["starter", "pro", "enterprise"]

for idx, tier_key in enumerate(tiers):
    tier_info = PRICING_TIERS[tier_key]
    
    with [col1, col2, col3][idx]:
        # Card styling
        is_current = current_tier == tier_key
        border_color = "#3b82f6" if is_current else "#e2e8f0"
        bg_color = "#eff6ff" if is_current else "#ffffff"
        
        st.markdown(f"""
        <div style="
            padding: 2rem;
            border: 2px solid {border_color};
            border-radius: 16px;
            background: {bg_color};
            height: 100%;
        ">
            <h2 style="margin: 0 0 0.5rem 0;">{tier_info['name']}</h2>
            <div style="font-size: 2.5rem; font-weight: 700; color: #3b82f6; margin: 1rem 0;">
                ${tier_info['price_monthly']}/mo
            </div>
            {f"<div style='color: #10b981; font-weight: 600; margin-bottom: 1rem;'>✓ Current Plan</div>" if is_current else ""}
            <p style="color: #64748b; margin-bottom: 1.5rem;">{tier_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features list
        st.markdown("**Features:**")
        features = tier_info.get("features", [])
        for feature in features[:8]:  # Show first 8 features
            st.markdown(f"✓ {feature.replace('_', ' ').title()}")
        
        if len(features) > 8:
            st.caption(f"+ {len(features) - 8} more features")
        
        # Limits
        limits = tier_info.get("limits", {})
        st.markdown("**Limits:**")
        st.caption(f"LLM Calls: {limits.get('llm_calls_per_month', 'N/A')}/month")
        st.caption(f"Users: {limits.get('max_users', 'N/A')}")
        
        # Action button
        if is_current:
            st.success("✅ Current Plan")
        else:
            if tier_key == "enterprise":
                if st.button("📞 Contact Sales", key=f"contact_{tier_key}", use_container_width=True):
                    st.info("💼 Please contact sales@aethersignal.com for enterprise pricing and custom solutions.")
            else:
                if st.button(f"Upgrade to {tier_info['name']}", key=f"upgrade_{tier_key}", use_container_width=True, type="primary"):
                    # In production, this would redirect to Stripe checkout
                    st.info(f"🚀 Redirecting to checkout for {tier_info['name']} plan...")
                    st.info("💡 In production, this would integrate with Stripe for secure payment processing.")

st.markdown("---")

# License key activation
st.markdown("## 🔑 Activate License Key")
st.caption("Enter your license key to activate your subscription")

license_key = st.text_input("License Key", type="password", key="license_key_input")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("Activate License", type="primary", use_container_width=True):
        if license_key:
            lm = LicenseManager()
            license_info = lm.load_license(license_key)
            
            st.success(f"✅ License activated! Plan: {license_info['tier'].title()}")
            st.rerun()
        else:
            st.error("Please enter a license key")

with col2:
    if st.button("Clear License", use_container_width=True):
        lm = LicenseManager()
        lm.clear_license()
        st.success("License cleared")
        st.rerun()

# Current subscription details
if current_info:
    st.markdown("---")
    st.markdown("## 📋 Current Subscription")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Plan", current_info.get("tier", "starter").title())
    
    with col2:
        st.metric("Status", "Active" if current_info.get("activated") else "Inactive")
    
    with col3:
        tier_limits = get_tier_info(current_tier).get("limits", {})
        st.metric("LLM Calls/Month", tier_limits.get("llm_calls_per_month", "N/A"))

