"""
AetherSignal – Quantum PV Explorer
Streamlit front-end: modularized with component-based architecture.
"""

import streamlit as st

from src.styles import apply_theme
from src.app_helpers import initialize_session
from src.ui import header, upload_section, query_interface, sidebar
from src.ui.results_display import display_query_results
from src.social_ae import render_social_ae_module


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AetherSignal – Quantum PV Explorer",
    page_icon="🔬",
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
# HEADER
# -------------------------------------------------------------------
header.render_header()
header.render_banner()


# -------------------------------------------------------------------
# STEP 1 – UPLOAD & SCHEMA
# -------------------------------------------------------------------
upload_section.render_upload_section()


# -------------------------------------------------------------------
# NEW MODULE – Social AE Explorer
# -------------------------------------------------------------------
with st.expander("🌐 Social AE Explorer (BETA)", expanded=False):
    render_social_ae_module()


# -------------------------------------------------------------------
# MAIN QUERY FLOW (only when data is loaded)
# -------------------------------------------------------------------
if st.session_state.data is not None and st.session_state.normalized_data is not None:
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


# -------------------------------------------------------------------
# SIDEBAR – Advanced filters & Quantum toggle
# -------------------------------------------------------------------
with st.sidebar:
    sidebar.render_sidebar()
