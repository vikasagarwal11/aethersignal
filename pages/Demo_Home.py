"""
Demo Home Page - Demo mode navigation hub
Wave 4: Public Demo Portal
"""

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.demo.demo_mode import is_demo_mode, exit_demo_mode, set_demo_mode
from src.demo.demo_loader import load_demo_data

# Page configuration
st.set_page_config(
    page_title="AetherSignal — Demo Mode",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# Apply theme
apply_theme()

# Top navigation - MUST BE FIRST st.* CALL AFTER apply_theme()
render_top_nav()

# Ensure demo mode is enabled (moved after nav render)
if not is_demo_mode():
    set_demo_mode(True)

# Load demo data into session state
if "demo_data_loaded" not in st.session_state:
    with st.spinner("Loading demo data..."):
        social_df, faers_df = load_demo_data()
        st.session_state.social_ae_data = social_df
        st.session_state.data = faers_df
        st.session_state.normalized_data = faers_df
        st.session_state.demo_data_loaded = True
        st.rerun()

# Demo mode banner
st.info("🚀 **You are in DEMO MODE** - Read-only demonstration with pre-loaded sample data. No data modifications allowed.")

# Main content
st.markdown("## 🚀 AetherSignal Live Demo")
st.caption("Explore the platform with pre-loaded sample data")

# Navigation cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="padding: 2rem; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                border-radius: 16px; color: white; text-align: center; cursor: pointer;"
         onclick="window.location.href='/Executive_Dashboard'">
        <h2 style="color: white; margin: 0 0 1rem 0;">📊</h2>
        <h3 style="color: white; margin: 0 0 0.5rem 0;">Executive Dashboard</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0;">Multi-source safety intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Executive Dashboard", use_container_width=True, key="demo_exec"):
        st.switch_page("pages/99_Executive_Dashboard.py")

with col2:
    st.markdown("""
    <div style="padding: 2rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                border-radius: 16px; color: white; text-align: center;">
        <h2 style="color: white; margin: 0 0 1rem 0;">🌐</h2>
        <h3 style="color: white; margin: 0 0 0.5rem 0;">Social AE Explorer</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0;">Real-time patient-reported AEs</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Explore Social AE", use_container_width=True, key="demo_social"):
        st.switch_page("pages/2_Social_AE_Explorer.py")

with col3:
    st.markdown("""
    <div style="padding: 2rem; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                border-radius: 16px; color: white; text-align: center;">
        <h2 style="color: white; margin: 0 0 1rem 0;">⚛️</h2>
        <h3 style="color: white; margin: 0 0 0.5rem 0;">Quantum PV Explorer</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0;">FAERS analysis with quantum ranking</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Explore Quantum PV", use_container_width=True, key="demo_quantum"):
        st.switch_page("pages/1_Quantum_PV_Explorer.py")

# Exit demo button
st.markdown("---")
if st.button("🚪 Exit Demo Mode", use_container_width=True):
    exit_demo_mode()
    st.switch_page("pages/Demo_Landing.py")

