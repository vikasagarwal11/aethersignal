"""
Enhanced Sidebar (CHUNK 7.9 + Sidebar Redesign)
Modern enterprise sidebar with organized sections for all AetherSignal features.
"""
import streamlit as st
from typing import Dict, Optional

# Import existing sidebar to preserve functionality
try:
    from src.ui.sidebar import render_sidebar as render_base_sidebar
except ImportError:
    render_base_sidebar = None

# Import new components
try:
    from src.ui.offline_mode_indicator import render_offline_mode_indicator
    OFFLINE_INDICATOR_AVAILABLE = True
except ImportError:
    OFFLINE_INDICATOR_AVAILABLE = False


def render_enhanced_sidebar(show_offline_indicator: bool = True) -> None:
    """
    Render enhanced sidebar with organized sections.
    
    Args:
        show_offline_indicator: Whether to show offline mode indicator
    """
    # Authentication section (preserve from original)
    try:
        from src.auth.auth import is_authenticated, get_current_user
        is_authed = is_authenticated()
        user = get_current_user() if is_authed else None
    except Exception:
        is_authed = st.session_state.get("authenticated", False)
        user = None
    
    if not is_authed:
        if st.button("🔐 Login", key="sidebar_login", use_container_width=True):
            st.switch_page("pages/Login.py")
        if st.button("📝 Register", key="sidebar_register", use_container_width=True):
            st.switch_page("pages/Register.py")
    else:
        user_email = user.get('email', '') if user else st.session_state.get('user_email', 'Unknown')
        st.caption(f"Signed in as {user_email}")
        if st.button("👤 Profile", key="sidebar_profile", use_container_width=True):
            st.switch_page("pages/Profile.py")
    
    st.markdown("---")
    
    # Offline Mode Indicator
    if show_offline_indicator and OFFLINE_INDICATOR_AVAILABLE:
        render_offline_mode_indicator()
        st.markdown("---")
    
    # 📁 Datasets Section
    with st.expander("📁 Datasets", expanded=False):
        if st.button("📤 Upload / Manage Files", key="sidebar_upload", use_container_width=True):
            st.session_state.show_upload = True
            st.rerun()
        
        if st.button("💾 Local Cache", key="sidebar_cache", use_container_width=True):
            st.session_state.show_cache_management = True
        
        data_loaded = st.session_state.get("normalized_data") is not None
        if data_loaded:
            df = st.session_state.get("normalized_data")
            if df is not None:
                st.caption(f"✅ Loaded: {len(df):,} rows")
    
    st.markdown("---")
    
    # 📊 Analytics Section
    with st.expander("📊 Analytics", expanded=False):
        data_loaded = st.session_state.get("normalized_data") is not None
        
        if st.button("📈 Trend Engine", key="sidebar_trends", use_container_width=True, disabled=not data_loaded):
            st.session_state.show_trend_alerts = True
            st.session_state.active_tab = "trend_alerts"
            st.rerun()
        
        if st.button("⚛️ Case Clustering", key="sidebar_clustering", use_container_width=True, disabled=not data_loaded):
            st.session_state.show_clustering = True
            st.rerun()
        
        if st.button("🔍 Duplicate Signals", key="sidebar_duplicates", use_container_width=True, disabled=not data_loaded):
            st.session_state.show_duplicates = True
            st.rerun()
        
        if st.button("🔗 Correlation Matrix", key="sidebar_correlation", use_container_width=True, disabled=not data_loaded):
            st.session_state.show_correlation = True
            st.rerun()
        
        if st.button("🔥 Portfolio Heatmaps", key="sidebar_heatmaps", use_container_width=True, disabled=not data_loaded):
            st.session_state.show_heatmaps = True
            st.rerun()
        
        if not data_loaded:
            st.caption("💡 Upload data to enable analytics")
    
    st.markdown("---")
    
    # 🧠 AI Assistance Section
    with st.expander("🧠 AI Assistance", expanded=False):
        if st.button("💬 AI Chat", key="sidebar_chat", use_container_width=True):
            st.session_state.show_chat = True
            st.session_state.active_tab = "conversational"
            st.rerun()
        
        if st.button("🔍 Inspector Mode", key="sidebar_inspector", use_container_width=True):
            st.session_state.show_inspector = True
            st.session_state.active_tab = "inspector_qa"
            st.rerun()
        
        if st.button("🛡️ Governance Dashboard", key="sidebar_governance", use_container_width=True):
            st.session_state.show_governance = True
            st.session_state.active_tab = "governance"
            st.rerun()
        
        if st.button("📊 Portfolio Intelligence", key="sidebar_portfolio", use_container_width=True):
            st.session_state.show_portfolio = True
            st.session_state.active_tab = "portfolio"
            st.rerun()
    
    st.markdown("---")
    
    # 📄 Signal Docs Section
    with st.expander("📄 Signal Docs", expanded=False):
        if st.button("📋 Signal File Builder", key="sidebar_signal_file", use_container_width=True):
            st.session_state.show_signal_file = True
            st.rerun()
        
        if st.button("📝 Label Impact", key="sidebar_label", use_container_width=True):
            st.session_state.show_label_impact = True
            st.session_state.active_tab = "label_impact"
            st.rerun()
        
        if st.button("⚖️ Benefit-Risk", key="sidebar_benefit_risk", use_container_width=True):
            st.session_state.show_benefit_risk = True
            st.session_state.active_tab = "benefit_risk"
            st.rerun()
        
        if st.button("🛠️ CAPA Recommendations", key="sidebar_capa", use_container_width=True):
            st.session_state.show_capa = True
            st.session_state.active_tab = "capa"
            st.rerun()
    
    st.markdown("---")
    
    # 🛰 System Section
    with st.expander("🛰 System", expanded=False):
        if st.button("🗑️ Clear Cache", key="sidebar_clear_cache", use_container_width=True):
            try:
                from src.ui.offline_cache_bridge import clear_all_cache
                if clear_all_cache():
                    st.success("Cache cleared!")
                else:
                    st.error("Failed to clear cache")
            except Exception:
                st.info("Cache clearing not available")
        
        if st.button("⚡ Performance Stats", key="sidebar_perf", use_container_width=True):
            st.session_state.show_performance = True
        
        if st.button("📋 Audit Trail", key="sidebar_audit", use_container_width=True):
            st.session_state.show_audit_trail = True
    
    st.markdown("---")
    
    # Executive Dashboard Quick Link
    st.markdown("### 🏢 Executive View")
    if st.button("📊 Executive Dashboard", key="sidebar_executive", use_container_width=True, type="primary"):
        st.session_state.show_executive_dashboard = True
        st.rerun()
    
    st.markdown("---")
    
    # Preserve existing advanced search and quantum toggle from original sidebar
    # Call base sidebar for filters if available
    if render_base_sidebar:
        try:
            # Only render the filters/controls part, not the full sidebar
            st.markdown("### 🔍 Advanced Filters")
            # Filters will be handled by the base sidebar when called separately
        except Exception:
            pass
    
    st.markdown("---")
    st.caption("AetherSignal – Enterprise PV Intelligence Platform")
    st.caption("Version 2.0 – Hybrid & Offline Capable")


def render_sidebar(use_enhanced: bool = True) -> None:
    """
    Main sidebar renderer - can use enhanced or base version.
    
    Args:
        use_enhanced: Whether to use enhanced sidebar
    """
    if use_enhanced:
        render_enhanced_sidebar()
    elif render_base_sidebar:
        render_base_sidebar()
    else:
        st.sidebar.info("Sidebar not available")

