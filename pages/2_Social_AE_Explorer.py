"""
Social AE Explorer Page
Full-page module for exploring social media adverse events.
"""

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.app_helpers import initialize_session
from src.ui.top_nav import render_top_nav
from src.ui.header import render_header, render_banner
from src.social_ae import render_social_ae_module

# PHASE 1.2: Navigation action handling is now centralized in nav_handler.py
# No need for _handle_nav_actions() here - it's called from render_top_nav()

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Social AE Explorer – AetherSignal",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",  # Changed to expanded so sidebar toggle is always visible
    menu_items=None,
)


# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()


# -------------------------------------------------------------------
# TOP NAVIGATION - MUST BE FIRST st.* CALL AFTER apply_theme()
# -------------------------------------------------------------------
render_top_nav()


# -------------------------------------------------------------------
# Initialize session state
# -------------------------------------------------------------------
initialize_session()

# Check authentication (optional for Social AE - can be public)
# Uncomment below if you want to require authentication for Social AE
# if not is_authenticated():
#     st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
#     st.warning("⚠️ Please login to access the Social AE Explorer.")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("🔐 Login", use_container_width=True):
#             st.switch_page("pages/Login.py")
#     with col2:
#         if st.button("📝 Register", use_container_width=True):
#             st.switch_page("pages/Register.py")
#     st.stop()

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
render_header(page_type="social")
render_banner()


# -------------------------------------------------------------------
# WORKSPACE ROUTING – Route to different views based on sidebar selection
# -------------------------------------------------------------------
workspace = st.session_state.get("active_workspace", "explorer")

# For Social AE Explorer workspace, temporarily set workspace key for status bar display
# (We'll restore it after status bar renders, before routing)
original_workspace = workspace
if workspace == "explorer":
    st.session_state.active_workspace = "social_ae"

# -------------------------------------------------------------------
# STATUS BAR V2 (Single render - before workspace routing)
# -------------------------------------------------------------------
from src.ui.status_bar_v2 import render_status_bar_v2
render_status_bar_v2()

# Restore original workspace for routing logic
st.session_state.active_workspace = original_workspace
workspace = original_workspace

# Route to different workspaces
if workspace == "governance":
    # Governance & Audit Workspace
    try:
        from src.ui.unified_governance_dashboard import render_unified_governance_dashboard
        normalized_df = st.session_state.get("normalized_data")
        render_unified_governance_dashboard(
            trend_alerts=None,
            rpf_scores=None,
            confidence_scores=None,
            label_impact_scores=None,
            subgroup_scores=None,
            shmi_score=None,
            governance_gaps=None,
            timing_deviations=None,
            lifecycle_stage=None,
            capa_findings=None,
            summary=None,
            signals=None,
            medical_llm=None
        )
        st.stop()
    except Exception as e:
        st.error(f"Governance dashboard unavailable: {e}")
        st.info("Falling back to Social AE Explorer workspace.")
        workspace = "explorer"

elif workspace == "inspector":
    # Inspector Simulation Workspace
    try:
        from src.ui.inspector_qa_panel import render_inspector_qa_tab
        normalized_df = st.session_state.get("normalized_data")
        
        st.title("🔍 Inspector Simulation")
        st.caption("Regulatory inspection simulation and readiness assessment")
        
        render_inspector_qa_tab(
            signals=None,
            governance_package=None,
            df=normalized_df
        )
        st.stop()
    except Exception as e:
        st.error(f"Inspector simulation unavailable: {e}")
        st.info("Falling back to Social AE Explorer workspace.")
        workspace = "explorer"

elif workspace == "executive":
    # Executive Dashboard Workspace
    try:
        from src.ui.executive_dashboard_enhanced import render_executive_dashboard_enhanced
        normalized_df = st.session_state.get("normalized_data")
        
        st.title("📊 Executive Safety Dashboard")
        st.caption("C-suite portfolio view with KPIs, forecasting, and risk intelligence")
        
        render_executive_dashboard_enhanced(
            stats=None,
            trends=None,
            alerts=None,
            df=normalized_df
        )
        st.stop()
    except Exception as e:
        st.error(f"Executive dashboard unavailable: {e}")
        st.info("Falling back to Social AE Explorer workspace.")
        workspace = "explorer"

elif workspace == "quantum":
    # Quantum & Advanced Workspace
    st.title("⚛️ Quantum & Advanced Analytics")
    st.caption("Quantum-inspired ranking and experimental analytics")
    
    st.info("""
    **Quantum Tools Available:**
    - Quantum-inspired ranking (toggle in sidebar)
    - Quantum clustering (available in Case Clustering panel)
    - Quantum anomaly detection
    
    Navigate to Explorer workspace to use quantum features with Social AE data.
    """)
    
    data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None
    if data_loaded:
        st.success(f"✅ Data loaded: {len(st.session_state.normalized_data):,} rows available for quantum analysis.")
        if st.button("🚀 Switch to Explorer to use Quantum Ranking", use_container_width=True):
            st.session_state.active_workspace = "explorer"
            st.rerun()
    else:
        st.warning("Upload data first to enable quantum features.")
    
    st.stop()

elif workspace == "processing":
    # Processing & Offline Mode Workspace
    st.title("🧬 Processing & Offline Mode")
    st.caption("Control where computation runs: server, local, or hybrid")
    
    # Show current processing mode
    current_mode = st.session_state.get("processing_mode", "auto")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Mode", current_mode.title())
    with col2:
        data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None
        if data_loaded:
            df = st.session_state.normalized_data
            st.metric("Dataset Size", f"{len(df):,} rows")
        else:
            st.metric("Dataset Size", "Not loaded")
    with col3:
        try:
            from src.hybrid.hybrid_master_engine import HybridMasterEngine
            if "hybrid_master_engine" in st.session_state:
                engine = st.session_state.hybrid_master_engine
                st.metric("Engine Status", "Ready")
            else:
                st.metric("Engine Status", "Not initialized")
        except Exception:
            st.metric("Engine Status", "Unavailable")
    
    st.markdown("---")
    st.markdown("### Processing Mode Control")
    st.info(f"Current processing mode: **{current_mode}**")
    st.caption("Change processing mode in the sidebar under '🧬 Processing Mode' section.")
    
    st.markdown("---")
    st.markdown("### Offline Mode")
    try:
        from src.ui.offline_mode_indicator import render_offline_mode_indicator
        render_offline_mode_indicator()
    except Exception:
        st.info("Offline mode indicator not available.")
    
    st.markdown("---")
    st.markdown("### Hybrid Engine Status")
    try:
        browser_caps = st.session_state.get("browser_capabilities", {})
        if browser_caps:
            st.json(browser_caps)
        else:
            st.info("Browser capabilities not yet detected. Upload data to initialize hybrid engine.")
    except Exception:
        st.info("Hybrid engine status not available.")
    
    st.stop()

# If we reach here, workspace is "explorer" (default) - continue with Social AE flow
# (Workspace already set to "social_ae" above for status bar display)

# -------------------------------------------------------------------
# EXPERIMENTAL BANNER (Phase 2 - Feature Parity Notice)
# -------------------------------------------------------------------
st.info(
    "🧪 **Experimental** — Social AE Explorer is now powered by the same hybrid engine as Signal module. "
    "You can now use explainability, clustering, and cross-linking features here too!",
    icon="🧪"
)

# -------------------------------------------------------------------
# SOCIAL AE EXPLORER MODULE
# -------------------------------------------------------------------
st.markdown("## 🌐 Social AE Explorer")
st.caption(
    "Real-time patient-reported adverse events from Reddit, X, and patient forums. "
    "⚠️ Exploratory only - not validated for regulatory use."
)

# Render the full Social AE module (no expander wrapper)
render_social_ae_module()
