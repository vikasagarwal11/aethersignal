"""
AetherSignal – Landing Page
Multi-module platform for Pharmacovigilance exploration.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.auth.auth import is_authenticated


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AetherSignal – Landing Page",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="expanded",  # Show sidebar for navigation
)


# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()


# -------------------------------------------------------------------
# TOP NAVIGATION
# -------------------------------------------------------------------
render_top_nav()

# Handle login/register/profile page routing
if st.session_state.get("show_login"):
    st.switch_page("pages/Login.py")
if st.session_state.get("show_register"):
    st.switch_page("pages/Register.py")
if st.session_state.get("show_profile"):
    st.switch_page("pages/Profile.py")

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# LANDING PAGE CONTENT
# -------------------------------------------------------------------

# Add custom CSS for landing page buttons
st.markdown("""
<style>
.landing-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(59,130,246,0.5) !important;
}

.landing-button-social:hover {
    box-shadow: 0 12px 30px rgba(16,185,129,0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="text-align: center; padding: 4rem 1rem; max-width: 1000px; margin: 0 auto;">
    <h1 style="font-size: 3.5rem; background: linear-gradient(90deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem; font-weight: 700;">
        AetherSignal
    </h1>
    <h2 style="font-size: 1.8rem; color: #475569; margin: 1.5rem 0; font-weight: 600;">
        Quantum PV Explorer + Real-Time Social AE Intelligence
    </h2>
    <p style="font-size: 1.2rem; color: #64748b; line-height: 1.8; margin: 2rem 0;">
        Two groundbreaking tools in one platform:<br>
        <strong style="color: #334155;">• Quantum PV Explorer:</strong> Upload FAERS, Argus, or Veeva data → ask questions in plain English → discover hidden signals with quantum-inspired ranking<br>
        <strong style="color: #334155;">• Social AE Explorer:</strong> Automatically pull patient voices from Reddit & X every day → see what official reports miss
    </p>
</div>
""", unsafe_allow_html=True)

# CTA Buttons - Using Streamlit's native page navigation
button_col1, button_col2 = st.columns(2)

with button_col1:
    if st.button("⚛️ Launch Quantum PV Explorer", use_container_width=True, type="primary", key="btn_quantum"):
        st.switch_page("pages/1_Quantum_PV_Explorer.py")

with button_col2:
    if st.button("🌐 Open Social AE Explorer", use_container_width=True, type="primary", key="btn_social"):
        st.switch_page("pages/2_Social_AE_Explorer.py")

# Custom styling for buttons
st.markdown("""
<style>
div[data-testid="stButton"] > button[kind="primary"] {
    padding: 1.5rem 2rem !important;
    font-size: 1.2rem !important;
    border-radius: 16px !important;
    font-weight: 600 !important;
    height: auto !important;
    min-height: 60px !important;
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    box-shadow: 0 8px 25px rgba(59,130,246,0.25) !important;
}

div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(59,130,246,0.35) !important;
}
</style>
""", unsafe_allow_html=True)

# Key Features Section
st.markdown("""
<div style="margin-top: 5rem; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 16px; border: 1px solid #e2e8f0;">
    <h3 style="color: #1e293b; font-size: 1.5rem; margin-bottom: 1.5rem; text-align: center;">Key Features</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; text-align: left;">
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Natural Language Queries</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Ask questions in plain English. No SQL required.</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚛️</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Quantum-Inspired Ranking</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Discover hidden signals with advanced ranking algorithms.</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌐</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Social Media Intelligence</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Real-time patient-reported adverse events from social platforms.</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📄</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">One-Click PDF Reports</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Generate comprehensive reports instantly.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Disclaimer Footer
st.markdown("""
<div style="margin-top: 4rem; color: #64748b; font-size: 0.9rem; padding: 1.5rem; background: #f8fafc; border-radius: 12px; text-align: center;">
    <p style="margin: 0.5rem 0;">
        <strong>⚠️ Exploratory tool</strong> • Session-based • No data stored • Built with ❤️ for patient safety
    </p>
    <p style="margin: 0.5rem 0; font-size: 0.85rem;">
        Spontaneous reports are subject to under-reporting and bias; no incidence or causality implied.
    </p>
</div>
""", unsafe_allow_html=True)
