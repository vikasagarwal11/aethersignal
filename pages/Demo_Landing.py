"""
Demo Landing Page - Public demo portal entry point
Wave 4: Public Demo Portal
"""

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.demo.demo_mode import set_demo_mode

# Page configuration
st.set_page_config(
    page_title="AetherSignal — Public Demo",
    page_icon="🚀",
    layout="wide",  # Changed from "centered" for consistent full-width layout
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# Apply theme
apply_theme()

# Top navigation - MUST BE FIRST st.* CALL AFTER apply_theme()
render_top_nav()

# Landing page content
st.markdown("""
<div style="text-align: center; padding: 4rem 1rem; max-width: 1000px; margin: 0 auto;">
    <h1 style="font-size: 3.5rem; background: linear-gradient(90deg, #3b82f6, #8b5cf6); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               margin-bottom: 1rem; font-weight: 700;">
        AetherSignal
    </h1>
    <h2 style="font-size: 1.8rem; color: #475569; margin: 1.5rem 0; font-weight: 600;">
        Global AI Pharmacovigilance Platform
    </h2>
    <p style="font-size: 1.2rem; color: #64748b; line-height: 1.8; margin: 2rem 0;">
        Detect safety signals from FAERS, Social Media, PubMed, ClinicalTrials and 7+ sources.<br>
        <strong>Powered by Quantum Scoring, AI Reasoning, and Multi-Source Fusion.</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Demo entry button
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🚀 Enter Live Demo", use_container_width=True, type="primary"):
        set_demo_mode(True)
        st.switch_page("pages/Demo_Home.py")

# Features section
st.markdown("""
<div style="margin-top: 5rem; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
            border-radius: 16px; border: 1px solid #e2e8f0;">
    <h3 style="color: #1e293b; font-size: 1.5rem; margin-bottom: 1.5rem; text-align: center;">Demo Features</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; text-align: left;">
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Executive Dashboard</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Multi-source safety intelligence for executives</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌐</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Social AE Explorer</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Real-time patient-reported adverse events</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧠</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">AI Intelligence</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Spike detection, novelty detection, clustering</p>
        </div>
        <div style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚛️</div>
            <h4 style="color: #1e293b; margin: 0.5rem 0;">Quantum Scoring</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin: 0;">Advanced signal prioritization</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Disclaimer
st.markdown("""
<div style="margin-top: 4rem; color: #64748b; font-size: 0.9rem; padding: 1.5rem; 
            background: #f8fafc; border-radius: 12px; text-align: center;">
    <p style="margin: 0.5rem 0;">
        <strong>⚠️ Demo Mode</strong> • Read-only • Pre-loaded sample data • Built for demonstration purposes
    </p>
    <p style="margin: 0.5rem 0; font-size: 0.85rem;">
        For full access and production use, please contact us.
    </p>
</div>
""", unsafe_allow_html=True)

