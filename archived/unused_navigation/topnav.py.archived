"""
Top Navigation Bar - Global header with search and actions
"""

import streamlit as st
from .state import GlobalState
from .theme import get_theme_colors


def render_top_nav_bar():
    """
    Render the top navigation bar with search and global actions.
    """
    GlobalState.init()
    colors = get_theme_colors()
    
    # Top bar with search and actions
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <h2 style="margin: 0; color: {colors['text']};">🧭 AetherSignal</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Global search (placeholder for now)
        search_query = st.text_input(
            "🔍 Search",
            placeholder="Search drugs, reactions, signals...",
            key="global_search",
            label_visibility="collapsed"
        )
        if search_query:
            st.session_state["global_search_query"] = search_query
    
    with col3:
        # Theme toggle
        theme_mode = st.radio(
            "Theme",
            ["🌞", "🌙"],
            horizontal=True,
            key="theme_toggle",
            label_visibility="collapsed"
        )
        if theme_mode == "🌞":
            st.session_state["theme_mode"] = "light"
        else:
            st.session_state["theme_mode"] = "dark"
    
    with col4:
        # AI Copilot toggle
        if st.button("🤖 Copilot", key="toggle_copilot", use_container_width=True):
            st.session_state["copilot_open"] = not st.session_state.get("copilot_open", False)
            st.rerun()
    
    st.markdown("---")

