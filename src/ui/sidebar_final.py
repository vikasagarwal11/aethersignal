"""
Final Sidebar Design (Complete Redesign)
Enterprise sidebar with compact/expanded modes, pill badges, and full navigation.
"""
import streamlit as st
from typing import Dict, Optional, Literal


def render_final_sidebar(
    mode: Literal["compact", "expanded", "inspector"] = "expanded",
    show_offline_indicator: bool = True
) -> None:
    """
    Render final sidebar design with multiple modes.
    
    Args:
        mode: Sidebar mode ("compact", "expanded", "inspector")
        show_offline_indicator: Whether to show offline mode indicator
    """
    # Sidebar mode selector
    if "sidebar_mode" not in st.session_state:
        st.session_state.sidebar_mode = mode
    
    # Mode toggle (only in expanded mode)
    if mode == "expanded":
        sidebar_mode = st.sidebar.radio(
            "View Mode",
            options=["compact", "expanded", "inspector"],
            index=["compact", "expanded", "inspector"].index(st.session_state.sidebar_mode),
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.sidebar_mode = sidebar_mode
        st.sidebar.markdown("---")
    
    # Authentication (always shown)
    _render_auth_section()
    
    st.sidebar.markdown("---")
    
    # Offline Indicator
    if show_offline_indicator:
        try:
            from src.ui.offline_mode_indicator import render_offline_mode_indicator
            render_offline_mode_indicator()
            st.sidebar.markdown("---")
        except Exception:
            pass
    
    # Mode-specific rendering
    if st.session_state.sidebar_mode == "compact":
        _render_compact_sidebar()
    elif st.session_state.sidebar_mode == "inspector":
        _render_inspector_sidebar()
    else:  # expanded
        _render_expanded_sidebar()


def _render_auth_section() -> None:
    """Render authentication section."""
    try:
        from src.auth.auth import is_authenticated, get_current_user
        is_authed = is_authenticated()
        user = get_current_user() if is_authed else None
    except Exception:
        is_authed = st.session_state.get("authenticated", False)
        user = None
    
    if not is_authed:
        if st.sidebar.button("🔐 Login", key="sidebar_login", use_container_width=True):
            st.switch_page("pages/Login.py")
        if st.sidebar.button("📝 Register", key="sidebar_register", use_container_width=True):
            st.switch_page("pages/Register.py")
    else:
        user_email = user.get('email', '') if user else st.session_state.get('user_email', 'Unknown')
        st.sidebar.caption(f"👤 {user_email}")
        if st.sidebar.button("Profile", key="sidebar_profile", use_container_width=True):
            st.switch_page("pages/Profile.py")


def _render_compact_sidebar() -> None:
    """Render compact sidebar with icons only."""
    st.sidebar.markdown("### Navigation")
    
    # Quick actions as pill badges
    actions = [
        ("📊", "Dashboard", "show_dashboard"),
        ("📈", "Trends", "show_trends"),
        ("⚛️", "Signals", "show_signals"),
        ("🛡️", "Governance", "show_governance"),
        ("🔍", "Inspector", "show_inspector"),
    ]
    
    for icon, label, key in actions:
        if st.sidebar.button(f"{icon} {label}", key=key, use_container_width=True):
            st.session_state[key] = True
            st.rerun()


def _render_expanded_sidebar() -> None:
    """Render expanded sidebar with full navigation."""
    # Use existing enhanced sidebar
    try:
        from src.ui.sidebar_enhanced import render_enhanced_sidebar
        render_enhanced_sidebar(show_offline_indicator=False)  # Already rendered above
    except Exception:
        # Fallback to basic navigation
        st.sidebar.markdown("### 📁 Datasets")
        if st.sidebar.button("Upload Files", use_container_width=True):
            st.session_state.show_upload = True
        
        st.sidebar.markdown("### 📊 Analytics")
        if st.sidebar.button("Trend Engine", use_container_width=True):
            st.session_state.show_trends = True


def _render_inspector_sidebar() -> None:
    """Render inspector-focused sidebar."""
    st.sidebar.markdown("### 🔍 Inspector Mode")
    st.sidebar.caption("Regulatory inspection simulation and readiness assessment")
    
    # Inspector-specific actions
    if st.sidebar.button("🎯 Start Inspection", type="primary", use_container_width=True):
        st.session_state.show_inspector_simulation = True
    
    if st.sidebar.button("📄 Generate Report", use_container_width=True):
        st.session_state.show_inspector_report = True
    
    if st.sidebar.button("🏆 Readiness Score", use_container_width=True):
        st.session_state.show_readiness = True
    
    st.sidebar.markdown("---")
    
    # Quick access to governance
    st.sidebar.markdown("### Quick Links")
    links = [
        ("🛡️ Governance", "governance"),
        ("📋 Signal Files", "signal_files"),
        ("📊 Executive Dashboard", "executive"),
    ]
    
    for label, key in links:
        if st.sidebar.button(label, key=f"link_{key}", use_container_width=True):
            st.session_state[f"show_{key}"] = True
            st.rerun()

