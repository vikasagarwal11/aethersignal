"""
Intelligence Navigation - Navigation for Intelligence Suite
"""

import streamlit as st
from src.ui.layout.state import GlobalState


def render_intelligence_nav():
    """
    Render navigation for Intelligence Suite.
    
    Returns:
        Selected intelligence module name
    """
    GlobalState.init()
    
    st.sidebar.markdown("### 🔮 Intelligence Suite")
    
    choice = st.sidebar.radio(
        "Explore:",
        [
            "Mechanism Explorer",
            "Causality Explorer",
            "Label Intelligence",
            "Safety Copilot"
        ],
        key="intelligence_nav"
    )
    
    return choice

