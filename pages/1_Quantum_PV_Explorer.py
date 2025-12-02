"""
Quantum PV Explorer Page
Main module for FAERS data analysis with quantum-inspired ranking.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Restore authentication session first, before anything else
try:
    from src.auth.auth import restore_session
    restore_session()
except Exception:
    pass

from src.styles import apply_theme
from src.app_helpers import initialize_session
from src.ui.top_nav import render_top_nav
from src.ui import header, upload_section, query_interface, sidebar
from src.ui.results_display import display_query_results

# -------------------------------------------------------------------
# Sidebar actions listener helpers
# -------------------------------------------------------------------
def _handle_nav_actions():
    nav_action = st.session_state.get("nav_action")
    if nav_action == "login":
        st.switch_page("pages/Login.py")
    elif nav_action == "register":
        st.switch_page("pages/Register.py")
    elif nav_action == "profile":
        st.switch_page("pages/Profile.py")
    elif nav_action == "logout":
        try:
            from src.auth.auth import logout_user
            logout_user()
        except Exception:
            pass
        st.session_state.nav_action = None
        st.rerun()
    if "nav_action" in st.session_state:
        st.session_state.nav_action = None
from src.auth.auth import is_authenticated


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Quantum PV Explorer – AetherSignal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()


# -------------------------------------------------------------------
# Initialize session state
# -------------------------------------------------------------------
initialize_session()


# -------------------------------------------------------------------
# TOP NAVIGATION
# -------------------------------------------------------------------
render_top_nav()

# Check authentication
if not is_authenticated():
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.warning("⚠️ Please login to access the Quantum PV Explorer.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", use_container_width=True):
            st.switch_page("pages/Login.py")
    with col2:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("pages/Register.py")
    st.stop()

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
# SIDEBAR – Must render early to set workspace state
# -------------------------------------------------------------------
with st.sidebar:
    sidebar.render_sidebar()
    # Listen for nav actions from top nav (login/register/profile/logout)
    nav_action = st.session_state.get("nav_action")
    if nav_action == "login":
        st.switch_page("pages/Login.py")
    elif nav_action == "register":
        st.switch_page("pages/Register.py")
    elif nav_action == "profile":
        st.switch_page("pages/Profile.py")
    elif nav_action == "logout":
        try:
            from src.auth.auth import logout_user
            logout_user()
        except Exception:
            pass
        st.session_state.nav_action = None
        st.rerun()
    # Clear action
    if "nav_action" in st.session_state:
        st.session_state.nav_action = None


# -------------------------------------------------------------------
# WORKSPACE ROUTING – Route to different views based on sidebar selection
# -------------------------------------------------------------------
workspace = st.session_state.get("active_workspace", "explorer")

# Route to different workspaces
if workspace == "governance":
    # Governance & Audit Workspace
    
    try:
        from src.ui.unified_governance_dashboard import render_unified_governance_dashboard
        import pandas as pd
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
        st.info("Falling back to Explorer workspace.")
        workspace = "explorer"

elif workspace == "inspector":
    # Inspector Simulation Workspace
    
    try:
        from src.ui.inspector_qa_panel import render_inspector_qa_tab
        import pandas as pd
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
        st.info("Falling back to Explorer workspace.")
        workspace = "explorer"

elif workspace == "executive":
    # Executive Dashboard Workspace
    
    try:
        from src.ui.executive_dashboard_enhanced import render_executive_dashboard_enhanced
        import pandas as pd
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
        st.info("Falling back to Explorer workspace.")
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
    
    Navigate to Explorer workspace and enable quantum ranking in the sidebar to use quantum features.
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

# If we reach here, workspace is "explorer" (default) - continue with normal flow


# -------------------------------------------------------------------
# HEADER (Only shown in Explorer workspace)
# -------------------------------------------------------------------
header.render_header()
header.render_banner()

# -------------------------------------------------------------------
# STATUS BAR V2 (UX Improvement - shows active workspace & processing mode)
# -------------------------------------------------------------------
from src.ui.status_bar_v2 import render_status_bar_v2
render_status_bar_v2()


# -------------------------------------------------------------------
# STEP 1 – UPLOAD & SCHEMA (Explorer workspace)
# -------------------------------------------------------------------
# Add styled header for Step 1 (matching Step 2 style)
st.markdown("""
<div style='margin: 3rem 0 2rem 0; padding: 1rem; background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; border-left: 5px solid #3b82f6;'>
    <div style='display: flex; align-items: center; gap: 1rem;'>
        <div style='font-size: 2.5rem;'>📤</div>
        <div>
            <div style='color: #1e40af; margin: 0; font-size: 1.3rem; font-weight: 700; line-height: 1.4;'>
                Step 1: Upload Safety Dataset
            </div>
                <p style='color: #475569; margin: 0.5rem 0 0 0; font-size: 1rem;'>
                    Upload any safety data format (FAERS, Argus, Veeva, CSV, Excel, PDF, etc.) — no standard format required. We auto-detect and adapt to your structure.
                </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

upload_section.render_upload_section()


# -------------------------------------------------------------------
# MAIN QUERY FLOW (only when data is loaded)
# -------------------------------------------------------------------
# Debug: Show data status
data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None

if data_loaded:
    normalized_df = st.session_state.normalized_data
    
    # Merge with Social AE data if enabled
    if st.session_state.get("include_social_ae", False):
        try:
            from src.social_ae.social_ae_integration import load_social_ae_data, merge_faers_and_social_ae
            
            social_ae_df = load_social_ae_data(
                days_back=30,
                use_supabase=True,  # Use Supabase if available
                drug_filter=None  # Load all drugs
            )
            
            if social_ae_df is not None and not social_ae_df.empty:
                normalized_df = merge_faers_and_social_ae(
                    normalized_df,
                    social_ae_df,
                    social_weight=0.4  # 40% weight for social signals
                )
                st.session_state.social_ae_merged = True
                st.session_state.social_ae_count = len(social_ae_df)
            else:
                st.session_state.social_ae_merged = False
        except Exception as e:
            # Silently fail if Social AE not available
            st.session_state.social_ae_merged = False
    else:
        st.session_state.social_ae_merged = False

    # Add visual separator between Step 1 and Step 2
    st.markdown("""
    <div style='margin: 3rem 0 2rem 0; padding: 1rem; background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; border-left: 5px solid #3b82f6;'>
        <div style='display: flex; align-items: center; gap: 1rem;'>
            <div style='font-size: 2.5rem;'>➡️</div>
            <div>
                <div style='color: #1e40af; margin: 0; font-size: 1.3rem; font-weight: 700; line-height: 1.4;'>
                    Step 2: Query Your Data
                </div>
                <p style='color: #475569; margin: 0.5rem 0 0 0; font-size: 1rem;'>
                    Use natural language queries, drug watchlist, or advanced filters to explore your safety data.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render query interface with tabs
    query_interface.render_query_interface(normalized_df)

    # 3 – Results (shown in query tab)
    if st.session_state.show_results and st.session_state.last_filters:
        display_query_results(
            st.session_state.last_filters,
            st.session_state.last_query_text,
            normalized_df,
        )
        
        # Session diagnostics card (bottom of results)
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("#### 🔎 Session diagnostics")
        
        try:
            # Calculate diagnostics from current session
            diag_rows = len(normalized_df)
            diag_queries = len(st.session_state.get("query_history", []))
            active_filters_count = len(st.session_state.last_filters) if st.session_state.last_filters else 0
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Rows in session", f"{diag_rows:,}")
            with c2:
                st.metric("Queries run", diag_queries)
            with c3:
                st.metric("Active filters", active_filters_count)
                
            # Show some dataset stats
            if "drug_name" in normalized_df.columns:
                unique_drugs = normalized_df["drug_name"].nunique()
                st.caption(f"Dataset: {unique_drugs:,} distinct drugs, "
                          f"{normalized_df['reaction'].nunique() if 'reaction' in normalized_df.columns else 0:,} "
                          f"distinct reactions")
        except Exception:
            st.info("Session diagnostics not available")
        
        # Quick diagnostic for "No results" issues
        if st.session_state.last_filters:
            with st.expander("🔍 Debug: Why no results?", expanded=False):
                from src.signal_stats import apply_filters
                
                # Test individual filters
                st.write("**Testing filters individually:**")
                if 'drug' in st.session_state.last_filters:
                    drug_only = apply_filters(normalized_df, {'drug': st.session_state.last_filters['drug']})
                    st.write(f"- Drug filter alone: {len(drug_only):,} rows")
                    if len(drug_only) > 0 and 'drug_name' in drug_only.columns:
                        st.caption(f"  Sample drugs: {drug_only['drug_name'].head(3).tolist()}")
                
                if 'reaction' in st.session_state.last_filters:
                    reaction_only = apply_filters(normalized_df, {'reaction': st.session_state.last_filters['reaction']})
                    st.write(f"- Reaction filter alone: {len(reaction_only):,} rows")
                    if len(reaction_only) > 0 and 'reaction' in reaction_only.columns:
                        st.caption(f"  Sample reactions: {reaction_only['reaction'].head(3).tolist()}")
                
                # Check for exact matches
                if 'drug' in st.session_state.last_filters and 'drug_name' in normalized_df.columns:
                    drug_term = str(st.session_state.last_filters['drug']).lower()
                    exact_matches = normalized_df['drug_name'].astype(str).str.lower().str.contains(drug_term, na=False).sum()
                    st.write(f"- Exact drug matches (case-insensitive): {exact_matches:,} rows")
                
                if 'reaction' in st.session_state.last_filters and 'reaction' in normalized_df.columns:
                    reaction_term = str(st.session_state.last_filters['reaction']).lower()
                    exact_matches = normalized_df['reaction'].astype(str).str.lower().str.contains(reaction_term, na=False).sum()
                    st.write(f"- Exact reaction matches (case-insensitive): {exact_matches:,} rows")
        
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # Landing content when no data is loaded
    st.markdown(
        """
        <div style="margin-top:1.4rem;" class="block-card">
            <h3 style="margin-top:0;">Getting started</h3>
            <p style="font-size:0.95rem; color:#475569;">
                Upload a safety dataset in Step 1 to unlock natural language search,
                quantum-inspired ranking, and one-click PDF summaries.
            </p>
            <ol style="font-size:0.92rem; color:#475569; margin-left:1.2rem;">
                <li>Export your FAERS / Argus / Veeva / internal safety data as CSV or Excel.</li>
                <li>Upload the files using the uploader above and click <strong>"Load &amp; map data"</strong>.</li>
                <li>Use suggested queries or type your own question in Step 2.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Note: Sidebar is now rendered earlier (before workspace routing) to ensure
# workspace state is available before content rendering
