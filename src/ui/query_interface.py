"""
Query interface component for AetherSignal.
Step 2 query workbench: natural‑language query, data‑driven starter tiles,
saved queries, and recent history in a clean layout.
"""

from datetime import datetime
from typing import List, Tuple, Dict, Optional
import re

import streamlit as st

from src import nl_query_parser
from src import watchlist_tab
from src.query_correction import (
    suggest_query_corrections,
    get_corrected_query,
    find_top_candidates,
)


def _build_dynamic_starter_questions(
    normalized_df,
) -> Tuple[List[Tuple[str, str, str]], List[str], List[str], List[str], List[str]]:
    """
    Build data‑driven starter questions and top drug/reaction lists.

    Returns:
        (starter_questions, top_drugs, top_reactions, all_drugs, all_reactions)
        starter_questions: list of (title, query, icon)
        top_drugs: top 8 drugs by frequency
        top_reactions: top 8 reactions by frequency
        all_drugs: all unique drugs (sorted alphabetically)
        all_reactions: all unique reactions (sorted alphabetically)
    """
    starter_questions: List[Tuple[str, str, str]] = []
    top_drugs: List[str] = []
    top_reactions: List[str] = []
    all_drugs: List[str] = []
    all_reactions: List[str] = []

    if normalized_df is None or normalized_df.empty:
        starter_questions = [
            ("Serious cases", "Show all serious cases by drug and reaction", "🔴"),
            ("Trending reactions", "What are the top reactions?", "📈"),
            ("Demographics", "Show cases by patient demographics", "👥"),
        ]
        return starter_questions, top_drugs, top_reactions, all_drugs, all_reactions

    # Top drugs / reactions (used for both tiles and chips)
    if "drug_name" in normalized_df.columns:
        drug_series = normalized_df["drug_name"].astype(str).str.split("; ").explode()
        # Get top 8 for prominent display
        top_drugs = drug_series.value_counts().head(8).index.tolist()
        # Get ALL unique drugs (sorted alphabetically for searchability)
        all_drugs = sorted(drug_series.dropna().unique().tolist(), key=str.lower)
    if "reaction" in normalized_df.columns:
        reaction_series = normalized_df["reaction"].astype(str).str.split("; ").explode()
        # Get top 8 for prominent display
        top_reactions = reaction_series.value_counts().head(8).index.tolist()
        # Get ALL unique reactions (sorted alphabetically for searchability)
        all_reactions = sorted(reaction_series.dropna().unique().tolist(), key=str.lower)

    top_drug = top_drugs[0] if top_drugs else None
    top_reaction = top_reactions[0] if top_reactions else None

    # Dates
    most_recent_year = None
    comparison_year = None
    date_columns = ["report_date", "receive_date", "event_date", "onset_date"]
    date_col = next((c for c in date_columns if c in normalized_df.columns), None)

    if date_col:
        try:
            from src.utils import parse_date

            dates = normalized_df[date_col].dropna().head(1000)
            years: List[int] = []
            for val in dates:
                parsed = parse_date(str(val))
                if parsed:
                    years.append(parsed.year)
                if isinstance(val, str) and len(val) >= 4:
                    m = re.search(r"\b(19|20)\d{2}\b", val)
                    if m:
                        years.append(int(m.group(0)))
            if years:
                most_recent_year = max(years)
                oldest_year = min(years)
                years_ago = max(2, min(3, most_recent_year - oldest_year))
                comparison_year = most_recent_year - years_ago
        except Exception:
            most_recent_year = None
            comparison_year = None

    # Age stats
    elderly_threshold = None
    pediatric_age = None
    if "age" in normalized_df.columns:
        try:
            from src.utils import extract_age

            ages = normalized_df["age"].apply(extract_age).dropna().head(5000)
            if len(ages) > 0:
                p75 = float(ages.quantile(0.75))
                p25 = float(ages.quantile(0.25))
                elderly_threshold = int(p75) if p75 > 50 else 65
                pediatric_age = int(min(18, p25)) if p25 else 18
        except Exception:
            elderly_threshold = 65
            pediatric_age = 18

    has_serious = "serious" in normalized_df.columns or "seriousness" in normalized_df.columns
    has_fatal = "outcome" in normalized_df.columns or "outc_cod" in normalized_df.columns
    has_country = "country" in normalized_df.columns

    # Build starter questions using whatever metadata we have
    if top_drug and top_reaction:
        starter_questions.append(
            (
                "Serious cases",
                f"Show all serious cases with drug {top_drug} and reaction {top_reaction}",
                "🔴",
            )
        )
    else:
        starter_questions.append(
            ("Serious cases", "Show all serious cases by drug and reaction", "🔴")
        )

    if most_recent_year and comparison_year:
        starter_questions.append(
            (
                "Trending reactions",
                f"What reactions increased since {comparison_year} for drug {top_drug or 'all drugs'}?",
                "📈",
            )
        )
    else:
        starter_questions.append(
            ("Trending reactions", "What are the top reactions?", "📈")
        )

    if elderly_threshold and has_fatal:
        starter_questions.append(
            (
                "High‑risk elderly",
                f"Show serious cases in patients age {elderly_threshold}+ with fatal outcomes",
                "🧓",
            )
        )

    if pediatric_age:
        starter_questions.append(
            (
                "Pediatric cases",
                f"Show all cases in patients under {pediatric_age} years old",
                "👶",
            )
        )

    if has_country:
        starter_questions.append(
            (
                "Geographic analysis",
                "Show cases by country for serious outcomes",
                "🌍",
            )
        )

    # Cap to 5 tiles for clarity
    starter_questions = starter_questions[:5]
    return starter_questions, top_drugs, top_reactions, all_drugs, all_reactions


def render_nl_query_tab(normalized_df):
    """Step 2 – natural-language query workbench."""

    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    # Compact header
    st.markdown("### Ask a question")
    st.caption(
        "Type a question in plain English, or start from a suggested tile."
    )

    smart_search = st.checkbox(
        "✨ Smart search (typo correction + suggestions)",
        value=False,  # OFF by default to preserve existing behavior
        help="Correct likely typos for drugs/reactions and suggest alternatives.",
    )

    starter_questions, top_drugs, top_reactions, all_drugs, all_reactions = _build_dynamic_starter_questions(
        normalized_df
    )

    # Optimized layout: Main query box takes more prominence
    main_col, side_col = st.columns([2.2, 1])

    # ---------------- Main: query box (more prominent) ----------------
    with main_col:
        # Styled title for the query field
        st.markdown("""
        <div style='margin-bottom: 0.5rem;'>
            <label style='font-size: 0.9rem; font-weight: 600; color: #1e293b; display: block; margin-bottom: 0.4rem;'>
                Enter safety question
            </label>
        </div>
        """, unsafe_allow_html=True)
        
        # Wrapped text area with custom styling
        st.markdown('<div class="query-textarea-wrapper">', unsafe_allow_html=True)
        query_text = st.text_area(
            "",  # Empty label since we have custom title above
            value=st.session_state.get(
                "query_text", st.session_state.get("last_query_text", "")
            ),
            height=100,  # Reduced from 160 to save space
            key="query_input",
            label_visibility="collapsed",  # Hide default label
            placeholder=(
                "Ask anything about your safety data, for example:\n"
                "• Show serious cases with drug aspirin and reaction gastrointestinal bleeding since 2021\n"
                "• Find cases in women age 30–60 with fatal outcomes\n"
                "• Cases with drug X from 2020‑01‑01 to 2023‑12‑31"
            ),
            help=(
                "Tips: Use 'drug X', 'reaction Y', 'age 18-65', 'serious', "
                "'country US', 'since 2020', 'from 2020-01-01', 'until 2023-12-31'. "
                "Multiple reactions default to OR (matches any). Use 'and' explicitly for AND logic."
            ),
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Try to load data from database if not in session state
        if st.session_state.get("normalized_data") is None:
            try:
                from src.auth.auth import is_authenticated, get_current_user
                from src.pv_storage import load_pv_data
                
                if is_authenticated():
                    user = get_current_user()
                    if user:
                        user_id = user.get('user_id')
                        organization = user.get('organization', '')
                        
                        # Load data from database
                        df_from_db = load_pv_data(user_id, organization)
                        if df_from_db is not None and not df_from_db.empty:
                            st.session_state.normalized_data = df_from_db
                            st.session_state.data = df_from_db
                            st.info("📊 Loaded your data from database.")
            except Exception:
                # Continue without database if it fails
                pass
        
        run_query_enabled = (
            st.session_state.data is not None
            and st.session_state.normalized_data is not None
        )
        
        # Button row with AI checkbox inline
        btn_col, ai_col = st.columns([2, 1])
        with btn_col:
            run_query = st.button(
                "🚀 Run query",
                type="primary",
                use_container_width=True,
                disabled=not run_query_enabled,
                key="run_main_query",
            )
        with ai_col:
            # AI checkbox moved inline to save vertical space
            use_llm = st.checkbox(
                "🤖 AI-enhanced",
                value=st.session_state.get("use_llm", False),
                key="use_llm_checkbox",
                help=(
                    "⚠️ Privacy Notice: When enabled, AI features include:\n"
                    "• Enhanced query interpretation\n"
                    "• Literature summarization & insights\n"
                    "• Case narrative analysis\n"
                    "• Causal reasoning for signals\n"
                    "• Enhanced MedDRA mapping\n\n"
                    "Your data remains private, but query text and case narratives may be sent to external AI services "
                    "(OpenAI/Claude/Groq). Disable for full privacy."
                )
            )
            st.session_state.use_llm = use_llm

        if not run_query_enabled and query_text:
            st.info("ℹ️ Upload and load data first to run queries.")

        if run_query and query_text and run_query_enabled:
            with st.spinner("🔎 Interpreting your query…"):
                working_query = query_text
                applied_corrections: Optional[Dict[str, tuple]] = None

                # Smart typo correction (auto-apply when confident)
                if smart_search and normalized_df is not None:
                    suggestions = suggest_query_corrections(working_query, normalized_df)
                    if suggestions:
                        corrected = get_corrected_query(working_query, suggestions)
                        applied_corrections = suggestions
                        working_query = corrected
                        st.info(f"Did you mean: **{corrected}**")
                        st.session_state.last_query_corrections = suggestions

                # Use hybrid router (rule-based first, LLM fallback if enabled)
                try:
                    from src.ai.hybrid_router import route_query
                    filters, method, confidence = route_query(
                        working_query, 
                        normalized_df, 
                        use_llm=use_llm,
                        llm_confidence_threshold=0.6
                    )
                    # Store method for display
                    st.session_state.last_query_method = method
                    st.session_state.last_query_confidence = confidence
                except ImportError:
                    # Fallback to direct parser if AI module not available
                    filters = nl_query_parser.parse_query_to_filters(working_query, normalized_df)
                    st.session_state.last_query_method = "rule_based"
                    st.session_state.last_query_confidence = 1.0
                
                is_valid, error_msg = nl_query_parser.validate_filters(filters, normalized_df)

                # Keyword fallback if parsing failed
                if smart_search and (not is_valid or not filters):
                    drug_candidates = find_top_candidates(normalized_df, "drug_name")
                    react_candidates = find_top_candidates(normalized_df, "reaction")
                    st.warning(error_msg or "Could not understand the query. Showing top candidates.")
                    fallback_filters = {}
                    if drug_candidates:
                        fallback_filters["drug"] = drug_candidates[0]
                    if react_candidates:
                        fallback_filters["reaction"] = react_candidates[0]
                    if fallback_filters:
                        filters = fallback_filters
                        is_valid = True
                        st.info(f"Applying fallback: {filters}")
                
                if not is_valid:
                    st.error(
                        error_msg
                        or "Could not understand the query. Please refine your question."
                    )
                else:
                    # Save to history
                    history = st.session_state.get("query_history", [])
                    history.append(
                        {
                            "query_text": working_query,
                            "timestamp": datetime.now().isoformat(),
                            "source": "nl",
                            "corrected": bool(applied_corrections),
                        }
                    )
                    st.session_state.query_history = history[-10:]

                    st.session_state.last_query_text = working_query
                    st.session_state.last_filters = filters
                    st.session_state.last_query_source = "nl"
                    st.session_state.show_results = True
                    st.rerun()

        if st.session_state.get("last_query_text"):
            st.markdown("---")
            st.caption(
                f"🕒 Last query: *'{st.session_state.last_query_text}'* "
                f"(source: {st.session_state.get('last_query_source','nl')})"
            )

    # ---------------- Side: starter tiles, saved queries, history (compact) ----------------
    with side_col:
        # Starter tiles (compact)
        st.markdown("#### ⚡ Starter questions")
        if starter_questions:
            # Use smaller buttons in a more compact layout
            for idx, (title, query, icon) in enumerate(starter_questions):
                if st.button(
                    f"{icon} {title}",
                    key=f"starter_{idx}",
                    use_container_width=True,
                    help=query,
                ):
                    st.session_state.query_text = query
                    st.session_state.last_query_text = query
                    st.session_state.show_results = False
                    st.rerun()
        else:
            st.caption("Upload data to see suggestions.")

        # Quick chips for top drugs / reactions (compact)
        if top_drugs or top_reactions:
            st.markdown("---")
        if top_drugs:
            st.markdown("**💊 Top drugs**")
            # Show fewer drugs to save space
            for idx, drug in enumerate(top_drugs[:4]):
                if st.button(
                    drug,
                    key=f"drug_chip_{idx}",
                    use_container_width=True,
                ):
                    current = st.session_state.get("query_text", "")
                    # Check if this drug is already in the query to prevent duplicates
                    drug_lower = drug.lower()
                    current_lower = current.lower()
                    if drug_lower in current_lower and f"drug {drug_lower}" in current_lower:
                        # Drug already in query, don't add again
                        st.info(f"ℹ️ '{drug}' is already in your query")
                    else:
                        new_q = (
                            f"{current} drug {drug}".strip()
                            if current
                            else f"Show cases with drug {drug}"
                        )
                        st.session_state.query_text = new_q
                        st.rerun()
            
            # Browse all drugs (collapsible, less prominent)
            if all_drugs and len(all_drugs) > 6:
                with st.expander(f"🔍 Browse all drugs ({len(all_drugs)} total)", expanded=False):
                    selected_drugs = st.multiselect(
                        "Select drug(s) to add to query",
                        options=all_drugs,
                        default=[],
                        key="browse_all_drugs",
                        help="Select one or more drugs. They will be added to your query with OR logic.",
                    )
                    if selected_drugs:
                        current = st.session_state.get("query_text", "")
                        current_lower = current.lower()
                        new_drugs = []
                        for drug in selected_drugs:
                            drug_lower = drug.lower()
                            # Check if drug is already in query
                            if drug_lower not in current_lower or f"drug {drug_lower}" not in current_lower:
                                new_drugs.append(drug)
                        
                        if new_drugs:
                            # Add all new drugs with OR logic
                            drug_terms = " OR ".join([f"drug {d}" for d in new_drugs])
                            if current:
                                new_q = f"{current} OR {drug_terms}".strip()
                            else:
                                new_q = f"Show cases with {drug_terms}"
                            st.session_state.query_text = new_q
                            st.rerun()
                        else:
                            st.info("ℹ️ All selected drugs are already in your query")
        
        if top_reactions:
            st.markdown("**⚠️ Top reactions**")
            # Show fewer reactions to save space
            for idx, reaction in enumerate(top_reactions[:4]):
                if st.button(
                    reaction,
                    key=f"reaction_chip_{idx}",
                    use_container_width=True,
                ):
                    current = st.session_state.get("query_text", "")
                    # Check if this reaction is already in the query to prevent duplicates
                    reaction_lower = reaction.lower()
                    current_lower = current.lower()
                    if reaction_lower in current_lower and f"reaction {reaction_lower}" in current_lower:
                        # Reaction already in query, don't add again
                        st.info(f"ℹ️ '{reaction}' is already in your query")
                    else:
                        # Check if there's already a reaction in the query
                        has_reaction = "reaction" in current_lower
                        if has_reaction:
                            # Add with OR to make it explicit (default behavior is OR)
                            new_q = (
                                f"{current} OR reaction {reaction}".strip()
                                if current
                                else f"Show cases with reaction {reaction}"
                            )
                        else:
                            new_q = (
                                f"{current} reaction {reaction}".strip()
                                if current
                                else f"Show cases with reaction {reaction}"
                            )
                        st.session_state.query_text = new_q
                        st.rerun()
            
            # Browse all reactions (collapsible, less prominent)
            if all_reactions and len(all_reactions) > 6:
                with st.expander(f"🔍 Browse all reactions ({len(all_reactions)} total)", expanded=False):
                    selected_reactions = st.multiselect(
                        "Select reaction(s) to add to query",
                        options=all_reactions,
                        default=[],
                        key="browse_all_reactions",
                        help="Select one or more reactions. They will be added to your query with OR logic.",
                    )
                    if selected_reactions:
                        current = st.session_state.get("query_text", "")
                        current_lower = current.lower()
                        new_reactions = []
                        for reaction in selected_reactions:
                            reaction_lower = reaction.lower()
                            # Check if reaction is already in query
                            if reaction_lower not in current_lower or f"reaction {reaction_lower}" not in current_lower:
                                new_reactions.append(reaction)
                        
                        if new_reactions:
                            # Add all new reactions with OR logic
                            reaction_terms = " OR ".join([f"reaction {r}" for r in new_reactions])
                            if current:
                                # Check if there's already a reaction in the query
                                has_reaction = "reaction" in current_lower
                                if has_reaction:
                                    new_q = f"{current} OR {reaction_terms}".strip()
                                else:
                                    new_q = f"{current} {reaction_terms}".strip()
                            else:
                                new_q = f"Show cases with {reaction_terms}"
                            st.session_state.query_text = new_q
                            st.rerun()
                        else:
                            st.info("ℹ️ All selected reactions are already in your query")

        # Saved queries
        st.markdown("---")
        saved_queries = st.session_state.get("saved_queries", [])
        with st.expander("📁 Saved queries", expanded=False):
            if saved_queries:
                for i, sq in enumerate(saved_queries):
                    label = f"▶ {sq['name']}"
                    if st.button(label, key=f"run_saved_{i}", use_container_width=True):
                        st.session_state.query_text = sq["query_text"]
                        st.session_state.last_query_text = sq["query_text"]
                        st.session_state.last_filters = sq["filters"]
                        st.session_state.last_query_source = "saved"
                        st.session_state.show_results = True
                        st.rerun()
            else:
                st.caption("No saved queries yet.")

            save_name = st.text_input(
                "Name current query",
                key="save_query_name",
                placeholder="e.g., Semaglutide pancreatitis 2024",
            )
            can_save = bool(
                st.session_state.get("last_filters")
                and st.session_state.get("last_query_text")
            )
            if st.button(
                "💾 Save current query",
                key="save_query_button",
                use_container_width=True,
                disabled=not can_save,
            ):
                name = save_name.strip() or f"Query {datetime.now():%Y-%m-%d %H:%M}"
                saved = st.session_state.get("saved_queries", [])
                if any(sq["name"] == name for sq in saved):
                    st.warning("A saved query with that name already exists.")
                else:
                    saved.append(
                        {
                            "name": name,
                            "query_text": st.session_state.get("last_query_text", ""),
                            "filters": st.session_state.get("last_filters", {}),
                        }
                    )
                    st.session_state.saved_queries = saved[-15:]
                    st.success(f"✅ Saved: “{name}”")
                    st.rerun()
            
            # Export/Import queries
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # Export saved queries
                if saved_queries:
                    import json
                    export_data = {
                        "saved_queries": saved_queries,
                        "exported_at": datetime.now().isoformat(),
                        "version": "1.0",
                    }
                    export_json = json.dumps(export_data, indent=2)
                    st.download_button(
                        "📥 Export queries",
                        export_json,
                        f"aethersignal_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                        use_container_width=True,
                        help="Export all saved queries as JSON",
                    )
                else:
                    st.caption("No queries to export")
            
            with col2:
                # Import queries
                uploaded_file = st.file_uploader(
                    "📤 Import queries",
                    type=["json"],
                    key="import_queries_file",
                    help="Import saved queries from JSON file",
                )
                if uploaded_file:
                    try:
                        import json
                        import_data = json.loads(uploaded_file.read())
                        
                        if "saved_queries" in import_data:
                            imported = import_data["saved_queries"]
                            existing = st.session_state.get("saved_queries", [])
                            existing_names = {sq["name"] for sq in existing}
                            
                            # Merge, avoiding duplicates by name
                            merged = existing.copy()
                            added = 0
                            for query in imported:
                                if query["name"] not in existing_names:
                                    merged.append(query)
                                    existing_names.add(query["name"])
                                    added += 1
                            
                            st.session_state.saved_queries = merged[-15:]  # Keep last 15
                            if added > 0:
                                st.success(f"✅ Imported {added} new query/queries")
                            else:
                                st.info("ℹ️ No new queries imported (all already exist)")
                            st.rerun()
                        else:
                            st.error("Invalid query file format")
                    except Exception as e:
                        st.error(f"Error importing queries: {str(e)}")

        # Recent history
        history = st.session_state.get("query_history", [])
        with st.expander("📜 Recent queries", expanded=False):
            if history:
                history_rev = list(reversed(history[-5:]))
                if st.button(
                    "🗑️ Clear history",
                    key="clear_history",
                    use_container_width=True,
                ):
                    st.session_state.query_history = []
                    st.rerun()

                for i, entry in enumerate(history_rev):
                    preview = (
                        entry["query_text"][:60] + "…"
                        if len(entry["query_text"]) > 60
                        else entry["query_text"]
                    )
                    ts = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M")
                    label = f"{preview} ({ts})"
                    if st.button(label, key=f"history_use_{i}", use_container_width=True):
                        st.session_state.query_text = entry["query_text"]
                        st.rerun()
            else:
                st.caption("Run a query to see it here.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_advanced_search_tab():
    """Render advanced search tab."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Advanced search")
    st.info(
        "Use the sidebar filters for structured search, or use the Natural Language "
        "Query tab for free‑form questions."
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_query_interface(normalized_df):
    """Render main query interface with tabs."""
    query_tab, watchlist_tab_ui, advanced_tab = st.tabs(
        ["💬 Natural language query", "🔬 Drug watchlist", "⚙️ Advanced search"]
    )

    with query_tab:
        render_nl_query_tab(normalized_df)

    with watchlist_tab_ui:
        watchlist_tab.show_watchlist_tab()

    with advanced_tab:
        render_advanced_search_tab()
