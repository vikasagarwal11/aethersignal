"""
Query interface component for AetherSignal.
Handles natural language query tab and advanced search tab.
"""

from datetime import datetime
import streamlit as st

from src import nl_query_parser
from src import watchlist_tab


def render_nl_query_tab(normalized_df):
    """Render natural language query interface."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### 2️⃣ Ask a question")

    left, right = st.columns([1, 2])

    with left:
        st.markdown("#### 💡 Suggested queries")
        presets = [
            "Show all serious cases with drug aspirin and reaction gastrointestinal bleeding",
            "Find cases for drug semaglutide with reaction pancreatitis since 2021",
            "Show all cases of optic neuritis in women age 18-45 treated with monoclonal antibodies",
            "Find serious cases for patients age 18-65 with drug ibuprofen and reaction nausea in United States",
        ]
        preset = st.selectbox(
            "Try one:",
            [""] + presets,
            key="preset_selector",
        )
        run_preset_enabled = preset and st.session_state.data is not None and st.session_state.normalized_data is not None
        if preset and st.button("🚀 Run preset", key="run_preset", use_container_width=True, disabled=not run_preset_enabled):
            st.session_state.last_query_text = preset
            st.session_state.last_query_source = "nl"
            st.session_state.last_filters = nl_query_parser.parse_query_to_filters(preset)
            st.session_state.show_results = True
            st.rerun()
        
        # Query history (limited to last 5, in expander)
        if st.session_state.get("query_history"):
            st.markdown("---")
            with st.expander("📜 Query history (last 5)", expanded=False):
                history = st.session_state.query_history[-5:]  # Last 5 queries
                history_reversed = list(reversed(history))
                
                # Clear history button
                if st.button("🗑️ Clear history", key="clear_history", use_container_width=True):
                    st.session_state.query_history = []
                    st.rerun()
                
                if history_reversed:
                    st.markdown("---")
                    for i, q_entry in enumerate(history_reversed):
                        query_preview = q_entry["query_text"][:50] + "..." if len(q_entry["query_text"]) > 50 else q_entry["query_text"]
                        timestamp = datetime.fromisoformat(q_entry["timestamp"]).strftime("%H:%M:%S")
                        # Fill text area instead of auto-running
                        if st.button(f"📝 {query_preview} ({timestamp})", key=f"history_{i}", use_container_width=True):
                            st.session_state.query_text = q_entry["query_text"]  # Fill the text area
                            st.rerun()

    with right:
        st.markdown("#### 💬 Natural language search")
        
        st.markdown("<div class='nl-panel'>", unsafe_allow_html=True)
        
        # Autocomplete suggestions based on loaded data
        suggestions = []
        if normalized_df is not None:
            # Get unique drugs and reactions for autocomplete
            if "drug_name" in normalized_df.columns:
                top_drugs = normalized_df["drug_name"].value_counts().head(10).index.tolist()
                suggestions.extend([f"drug {d}" for d in top_drugs[:5]])
            if "reaction" in normalized_df.columns:
                top_reactions = normalized_df["reaction"].value_counts().head(10).index.tolist()
                suggestions.extend([f"reaction {r}" for r in top_reactions[:5]])
        
        if suggestions:
            with st.expander("💡 Quick suggestions", expanded=False):
                for suggestion in suggestions[:8]:
                    if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                        st.session_state.last_query_text = f"Show cases with {suggestion}"
                        st.session_state.last_query_source = "nl"
                        st.session_state.last_filters = nl_query_parser.parse_query_to_filters(
                            st.session_state.last_query_text
                        )
                        st.session_state.show_results = True
                        st.rerun()
        
        st.markdown("<div class='nl-textarea-shell'>", unsafe_allow_html=True)
        query_text = st.text_area(
            "Enter safety question…",
            value=st.session_state.get("query_text", st.session_state.get("last_query_text", "")),
            height=140,
            key="query_input",
            placeholder=(
                "e.g. 'Show all cases with drug aspirin and reaction headache' or "
                "'Find serious cases for patients age 18–65 in Japan since 2020'"
            ),
            help="Tips: Use 'drug X', 'reaction Y', 'age 18-65', 'serious', 'country US', 'since 2020'",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close nl-panel
        
        run_query_enabled = st.session_state.data is not None and st.session_state.normalized_data is not None
        run_query = st.button("🚀 Run query", type="primary", use_container_width=True, disabled=not run_query_enabled)
        
        if not run_query_enabled and query_text:
            st.info("ℹ️ Upload and load data first to run queries.")

        if run_query and query_text and run_query_enabled:
            with st.spinner("Interpreting your query…"):
                filters = nl_query_parser.parse_query_to_filters(query_text)
                is_valid, error_msg = nl_query_parser.validate_filters(filters)
                if not is_valid:
                    st.error(error_msg or "Invalid filters detected. Please refine your query.")
                else:
                    st.session_state.last_query_text = query_text
                    st.session_state.last_filters = filters
                    st.session_state.last_query_source = "nl"
                    st.session_state.show_results = True
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # Close block-card


def render_advanced_search_tab():
    """Render advanced search tab."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Advanced Search")
    st.info("💡 Use the sidebar filters for structured search, or use the Natural Language Query tab for free-form questions.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_query_interface(normalized_df):
    """Render main query interface with tabs."""
    # Create tabs for different query modes
    query_tab, watchlist_tab_ui, advanced_tab = st.tabs([
        "💬 Natural Language Query",
        "🔬 Drug Watchlist",
        "⚙️ Advanced Search"
    ])

    with query_tab:
        render_nl_query_tab(normalized_df)

    with watchlist_tab_ui:
        watchlist_tab.show_watchlist_tab()

    with advanced_tab:
        render_advanced_search_tab()

