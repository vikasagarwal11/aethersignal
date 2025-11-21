"""
Quantum PV Explorer Page
Main module for FAERS data analysis with quantum-inspired ranking.
"""

import streamlit as st

from src.styles import apply_theme
from src.app_helpers import initialize_session
from src.ui.top_nav import render_top_nav
from src.ui import header, upload_section, query_interface, sidebar
from src.ui.results_display import display_query_results


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

# Prevent flicker on page load
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


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
                <h3 style='color: #1e40af; margin: 0; font-size: 1.3rem; font-weight: 700;'>
                    Step 2: Query Your Data
                </h3>
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

