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


def _generate_fast_mode_response(
    query: str,
    filters: Dict,
    normalized_df,
    use_llm: bool = False
) -> str:
    """
    Generate a quick conversational response in FAST MODE.
    No data filtering or statistics - just a quick answer based on filters.
    """
    response_parts = []
    
    # Build quick response based on extracted filters
    if filters:
        # Drug mentioned
        if "drug" in filters:
            drug = filters["drug"]
            if isinstance(drug, list):
                drug = drug[0] if drug else "the specified drug"
            response_parts.append(f"I understand you're asking about **{drug}**.")
        else:
            response_parts.append("I understand your query.")
        
        # Reaction mentioned
        if "reaction" in filters:
            reaction = filters["reaction"]
            if isinstance(reaction, list):
                reaction = reaction[0] if reaction else "the specified reaction"
            if "drug" in filters:
                response_parts.append(f"You're interested in **{reaction}** associated with this drug.")
            else:
                response_parts.append(f"You're asking about cases involving **{reaction}**.")
        
        # Additional filters
        filter_parts = []
        if "age" in filters:
            age = filters["age"]
            if isinstance(age, dict):
                if "min" in age and "max" in age:
                    filter_parts.append(f"age {age['min']}-{age['max']}")
                elif "min" in age:
                    filter_parts.append(f"age {age['min']}+")
                elif "max" in age:
                    filter_parts.append(f"age ≤{age['max']}")
        if "serious" in filters and filters["serious"]:
            filter_parts.append("serious cases only")
        if "country" in filters:
            country = filters["country"]
            if isinstance(country, list):
                country = country[0] if country else ""
            filter_parts.append(f"from {country}")
        
        if filter_parts:
            response_parts.append(f"Additional criteria: {', '.join(filter_parts)}.")
        
        # Suggest full analysis
        response_parts.append(
            "\n💡 **Want detailed statistics?** Click '📊 Generate Full Analysis' below, then send your message again to get comprehensive results including PRR/ROR, trends, and case details."
        )
    else:
        # No filters extracted - generic response
        response_parts.append(
            "I understand your question. To provide specific insights, could you mention a drug name, reaction, or specific criteria? "
            "Or click '📊 Generate Full Analysis' and send your message again for comprehensive analysis."
        )
    
    # If LLM is enabled, try to enhance the response
    if use_llm:
        try:
            # Try to get a quick LLM response without filtering
            from src.ai.medical_llm import call_medical_llm
            
            prompt = f"""User Query: {query}

Extracted Filters: {filters}

Provide a brief, conversational response (2-3 sentences) explaining what the user is asking about based on the extracted filters. Do not generate statistics or numbers - just acknowledge understanding of the query.

Be helpful and suggest they use "Generate Full Analysis" for detailed results."""
            
            llm_response = call_medical_llm(
                prompt=prompt,
                system_prompt="You are a helpful pharmacovigilance assistant. Provide brief, conversational responses.",
                task_type="general",
                max_tokens=150,
                temperature=0.3
            )
            
            if llm_response and len(llm_response.strip()) > 20:
                return llm_response.strip() + "\n\n💡 **Want detailed statistics?** Click '📊 Generate Full Analysis' below, then send your message again."
        except Exception:
            pass  # Fall back to rule-based
    
    return "\n".join(response_parts)


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


def _pill_button(label: str, key: str, query_text: str):
    """
    Universal clickable pill component (Chunk 4D).
    Sets pending_user_text instead of sending immediately.
    
    Args:
        label: Display text for the pill
        key: Unique key for Streamlit button
        query_text: Text to auto-fill into chat input when clicked
    """
    if st.button(
        label,
        key=key,
        use_container_width=True,
        type="secondary",
        help=query_text if len(query_text) > len(label) else None
    ):
        st.session_state.pending_user_text = query_text
        st.rerun()


def _build_suggestions_panel(normalized_df, on_send_callback):
    """
    Build unified suggestions panel with pill-styled buttons (Chunk 3B + 4C/4E).
    Includes: Starter Questions, Top Drugs, Top Reactions, Saved Queries, Recent Queries.
    Pills now auto-fill chat input instead of sending immediately (Chunk 4).
    
    Args:
        normalized_df: DataFrame for data-driven suggestions
        on_send_callback: Function to call when user sends message (not used here, kept for compatibility)
    """
    # Get data-driven suggestions
    starter_questions, top_drugs, top_reactions, all_drugs, all_reactions = _build_dynamic_starter_questions(
        normalized_df
    )

    # Create tabs for different suggestion categories
    suggestion_tabs = st.tabs([
        "⭐ Starter Prompts",
        "💊 Top Drugs",
        "⚠️ Top Reactions",
        "📌 Saved Queries",
        "🕒 Recent Queries"
    ])
    
    # Tab 1: Starter Prompts (Chunk 4E)
    with suggestion_tabs[0]:
        if starter_questions:
            cols_per_row = 3
            for row_start in range(0, min(6, len(starter_questions)), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    idx = row_start + col_idx
                    if idx < len(starter_questions):
                        title, query, icon = starter_questions[idx]
                        with cols[col_idx]:
                            _pill_button(
                                f"{icon} {title}",
                                f"starter-{idx}-{hash(query)}",
                                query
                            )
        else:
            st.info("Upload data to see starter questions.")
    
    # Tab 2: Top Drugs (Chunk 4E)
    with suggestion_tabs[1]:
        if top_drugs:
            display_drugs = top_drugs[:12]
            cols_per_row = 4
            for row_start in range(0, len(display_drugs), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    idx = row_start + col_idx
                    if idx < len(display_drugs):
                        drug = display_drugs[idx]
                        query_text = f"Show me safety information for {drug}"
                        with cols[col_idx]:
                            _pill_button(
                                drug,
                                f"drug-{idx}-{hash(drug)}",
                                query_text
                            )
        else:
            st.info("No drug data available.")
    
    # Tab 3: Top Reactions (Chunk 4E)
    with suggestion_tabs[2]:
        if top_reactions:
            display_reactions = top_reactions[:12]
            cols_per_row = 4
            for row_start in range(0, len(display_reactions), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    idx = row_start + col_idx
                    if idx < len(display_reactions):
                        reaction = display_reactions[idx]
                        query_text = f"Cases involving {reaction}"
                        with cols[col_idx]:
                            _pill_button(
                                reaction,
                                f"reaction-{idx}-{hash(reaction)}",
                                query_text
                            )
        else:
            st.info("No reaction data available.")
    
    # Tab 4: Saved Queries (Chunk 4E)
    with suggestion_tabs[3]:
        saved = st.session_state.get("saved_queries", [])
        if saved:
            for idx, sq in enumerate(saved[:10]):
                query_text = sq.get("query_text", sq) if isinstance(sq, dict) else sq
                name = sq.get("name", f"Query {idx+1}") if isinstance(sq, dict) else query_text[:50]
                _pill_button(
                    f"▶ {name}",
                    f"saved-{idx}-{hash(str(sq))}",
                    query_text
                )
        else:
            st.info("No saved queries yet. Save queries from the results section.")
    
    # Tab 5: Recent Queries (Chunk 4E)
    with suggestion_tabs[4]:
        recent = st.session_state.get("query_history", [])
        if recent:
            display_recent = list(reversed(recent[-10:]))
            for idx, rq in enumerate(display_recent):
                query_text = rq.get("query_text", "") if isinstance(rq, dict) else rq
                if query_text:
                    display_text = query_text[:60] + "..." if len(query_text) > 60 else query_text
                    _pill_button(
                        f"▶ {display_text}",
                        f"recent-{idx}-{hash(query_text)}",
                        query_text
                    )
        else:
            st.info("No recent queries yet. Start asking questions above!")


def render_nl_query_tab(normalized_df):
    """
    NEW Chat-First Natural Language Query Tab (Option A2).
    Replaces old text-area interface with a full conversational UI.
    
    All existing features are preserved:
    - Starter questions (collapsible)
    - Top drugs / reactions (collapsible)
    - Saved queries / recent queries (collapsible)
    - LLM-enhanced toggle & Smart Search toggle
    """
    
    from src.ui.chat_interface import render_chat_interface, add_chat_message, update_last_assistant_message
    from src.ai.conversational_engine import process_conversational_query
    from src.ai.stream_helpers import send_stream_step, finalize_assistant_message
    from src import signal_stats
    
    # Ensure chat history exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "run_in_progress" not in st.session_state:
        st.session_state.run_in_progress = False
    
    st.markdown("### 💬 Chat-Based Safety Search")

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
                    normalized_df = df_from_db  # Update local reference
        except Exception:
            pass
        
    # Check if data is available
    data_available = (
            st.session_state.data is not None
            and st.session_state.normalized_data is not None
        and normalized_df is not None
        and not normalized_df.empty
    )
    
    if not data_available:
        st.warning("⚠️ Please upload and load data first to use the chat interface.")
    
    # Processing callback - called when user hits Send button in chat
    def on_send(user_message: str):
        """Safe handler for processing chat messages with timeout + heartbeat."""
        if not data_available:
            add_chat_message("assistant", "⚠️ Please upload and load data first to use the chat interface.")
            st.rerun()
            return
        
        # 1. Add user message to history
        add_chat_message("user", user_message)
        
        # Show AI is "thinking"
        add_chat_message("assistant", "Analyzing your query…", status="thinking")
        
        # Refresh the UI to show the thinking bubble immediately
        st.rerun()
        
        # Start pipeline
        st.session_state.run_in_progress = True
        
        # Get settings
        use_smart_search = st.session_state.get("use_smart_search", True)
        use_llm = st.session_state.get("enable_ai_enhanced", False)
        
        query = user_message.strip()
        
        # CHUNK 6.13: Check for SAR generation request
        query_lower = query.lower()
        is_sar_request = any(keyword in query_lower for keyword in [
            "generate sar", "create sar", "safety assessment report", "assessment report",
            "generate report", "create report", "full report", "sar report",
            "draft prac report", "regulatory report", "signal assessment"
        ])
        
        # CHUNK 6.14: Check for DSUR/PBRER generation request
        is_dsur_request = any(keyword in query_lower for keyword in [
            "generate dsur", "create dsur", "development safety update", "dsur report",
            "dsur", "clinical trial safety report"
        ])
        
        is_pbrer_request = any(keyword in query_lower for keyword in [
            "generate pbrer", "create pbrer", "periodic benefit-risk", "benefit risk evaluation",
            "pbrer report", "pbrer", "periodic evaluation report", "post-marketing report"
        ])
        
        # CHUNK 6.15: Check for CAPA generation request
        is_capa_request = any(keyword in query_lower for keyword in [
            "capa", "corrective action", "preventive action", "regulatory next steps",
            "what actions should we take", "mitigate risk", "how do we address",
            "risk minimization", "rmm", "compliance actions"
        ]) and "inspection" not in query_lower  # Exclude inspection requests
        
        # CHUNK 6.16: Check for Inspection Readiness request
        is_inspection_request = any(keyword in query_lower for keyword in [
            "inspection", "audit", "inspection readiness", "audit binder", "audit defense",
            "prepare evidence", "fda inspection", "ema inspection", "inspector questions",
            "simulate inspection", "regulatory inspection", "audit trail",
            "inspection evidence", "what do we need to prepare"
        ])
        
        # CHUNK 6.18: Check for CSP generation request
        is_csp_request = any(keyword in query_lower for keyword in [
            "csp", "core safety profile", "company core safety information",
            "ccsi", "generate csp", "what are the important identified risks",
            "important potential risks", "missing information",
            "is an important identified risk", "rmp annex 1", "safety specification"
        ]) and "label" not in query_lower and "smpc" not in query_lower and "uspi" not in query_lower  # Exclude label impact requests and "label" not in query_lower  # Exclude label impact requests
        
        # CHUNK 6.19: Check for Label Impact Assessment request
        is_label_impact_request = any(keyword in query_lower for keyword in [
            "label impact", "label update", "label change", "smpc", "uspi", "ccds",
            "does this signal require a label update", "draft eu smpc", "draft smpc warnings",
            "create uspi wording", "generate ccds safety wording", "section 4.4", "section 4.8",
            "boxed warning", "warnings and precautions", "adverse reactions table",
            "labeling update", "label revision", "label modification"
        ])
        
        # Smart Search Correction (with timeout protection)
        if use_smart_search and normalized_df is not None:
            try:
                from src.ai.safe_executor import run_with_timeout
                status, suggestions_result = run_with_timeout(
                    suggest_query_corrections,
                    5.0,  # timeout_seconds as positional
                    query,
                    normalized_df
                )
                
                if status == "success" and suggestions_result:
                    corrected = get_corrected_query(query, suggestions_result)
                    if corrected.strip().lower() != query.strip().lower():
                        update_last_assistant_message(
                            f"Analyzing your query… (corrected to: **{corrected}**)", 
                            status="thinking"
                        )
                        query = corrected
            except Exception:
                # If correction fails, continue with original query
                pass
        
        # Placeholder for heartbeat progress updates
        status_box = st.empty()
        
        try:
            # Import timeout and heartbeat utilities
            from src.ai.safe_executor import run_with_timeout
            from src.ai.heartbeat import heartbeat
            from src.ai.hybrid_router import route_query
            from src import signal_stats
            
            # 2. Start heartbeat updates
            heartbeat("Understanding your question", status_box)
            
            # 3. Run the hybrid router with timeout (12 seconds)
            heartbeat("Extracting intent", status_box)
            status, router_output = run_with_timeout(
                route_query,
                12.0,
                query,
                        normalized_df, 
                use_llm
            )
            
            if status == "timeout":
                finalize_assistant_message(
                    "⏳ The query interpretation took too long. Try refining your question or using simpler terms.",
                    metadata={"error": "timeout", "step": "routing"}
                )
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            if status == "error":
                finalize_assistant_message(
                    f"⚠️ I encountered an error understanding your question: {router_output}",
                    metadata={"error": str(router_output), "step": "routing"}
                )
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            # router_output is a tuple: (filters, method, confidence)
            filters, method, confidence = router_output
            
            # Get analysis mode (default to "fast")
            analysis_mode = st.session_state.get("analysis_mode", "fast")
            
            # ---------------------------------------------------------------------
            # FAST MODE (chat only - no heavy processing) - CHUNK 6.6
            # ---------------------------------------------------------------------
            if analysis_mode == "fast":
                heartbeat("Generating conversational response", status_box)
                
                # CHUNK 6.6: Generate quick_results for fast mode insights
                quick_results = {}
                try:
                    from src.ai.followup_logic import followup_analysis
                    # Get current memory state
                    memory_state = st.session_state.get("memory_state", {})
                    # Generate quick insights (lightweight, fast)
                    quick_results = followup_analysis(normalized_df, memory_state, include_all=True)
                except Exception:
                    # If follow-up analysis fails, continue without insights
                    pass
                
                # Generate quick response without filtering/statistics
                fast_response = _generate_fast_mode_response(query, filters, normalized_df, use_llm)
                
                finalize_assistant_message(
                    fast_response,
                    metadata={
                        "filters": filters,
                        "method": method,
                        "confidence": confidence,
                        "mode": "fast",
                        "quick_results": quick_results  # CHUNK 6.6: Include quick insights
                    }
                )
                
                # Don't store results or trigger display
                st.session_state.show_results = False
                st.session_state.last_filters = None  # Clear to prevent accidental display
                
                # Store last query for potential full analysis later
                st.session_state.last_query_text = query
                
                # CHUNK 6.7: Store quick_results for debug panel
                if "quick_results" in metadata:
                    st.session_state.last_quick_results = metadata["quick_results"]
                
                # Save to query history (session + database)
                history = st.session_state.get("query_history", [])
                history.append({
                    "query_text": query,
                    "timestamp": datetime.now().isoformat(),
                    "source": "chat_fast",
                })
                st.session_state.query_history = history[-10:]
                
                # Also persist to database
                try:
                    from src.auth.auth import is_authenticated, get_current_user
                    from src.query_persistence import save_query_to_history
                    import time
                    
                    if is_authenticated():
                        user = get_current_user()
                        if user:
                            user_id = user.get('user_id')
                            organization = user.get('organization', '')
                            
                            save_query_to_history(
                                user_id=user_id,
                                organization=organization,
                                query_text=query,
                                filters=st.session_state.get("last_filters"),
                                source="nl",
                                results_count=len(filtered_df) if 'filtered_df' in locals() else None,
                                execution_time_ms=None
                            )
                except Exception:
                    pass  # Don't break query execution if persistence fails
                
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            # ---------------------------------------------------------------------
            # FULL MODE (heavy pipeline - runs complete analysis)
            # ---------------------------------------------------------------------
            
            heartbeat("Applying filters to your data", status_box)
            
            # 4. Filtering with timeout (18 seconds for full mode)
            status, filtered_df_result = run_with_timeout(
                signal_stats.apply_filters,
                18.0,
                normalized_df,
                filters
            )
            
            if status == "timeout":
                finalize_assistant_message(
                    "⏳ Filtering your data took too long. Try narrowing your query or reducing the dataset size.",
                    metadata={"error": "timeout", "step": "filtering", "filters": filters}
                )
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            if status == "error":
                finalize_assistant_message(
                    f"⚠️ Error applying filters: {filtered_df_result}",
                    metadata={"error": str(filtered_df_result), "step": "filtering", "filters": filters}
                )
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            filtered_df = filtered_df_result
            
            if filtered_df.empty:
                finalize_assistant_message(
                    "No cases found matching your query. Please try adjusting your search criteria.",
                    metadata={"filters": filters, "method": method, "confidence": confidence}
                )
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            heartbeat("Running full safety analysis", status_box)
            
            # 5. Generate full conversational response using existing engine
            # Use process_conversational_query which handles everything properly
            heartbeat("Generating summary", status_box)
            
            # Run the full pipeline with timeout (30 seconds for complete analysis)
            status, result = run_with_timeout(
                process_conversational_query,
                30.0,
                query,
                normalized_df,
                use_llm
            )
            
            if status == "timeout":
                # Generate a response from filtered data (we have at least that)
                partial_response = (
                    f"I found **{len(filtered_df):,} cases** matching your query, but the full statistical analysis is taking longer than expected. "
                    f"The results below show the filtered cases, but some statistics may be incomplete."
                )
                finalize_assistant_message(
                    partial_response,
                    metadata={
                        "filters": filters,
                        "method": method,
                        "confidence": confidence,
                        "filtered_df_size": len(filtered_df),
                        "partial": True
                    }
                )
                # Store filtered data for results display
                st.session_state.last_filters = filters
                st.session_state.last_query_text = query
                st.session_state.last_query_source = "chat"
                # Store filtered_df for results display (even if partial)
                if 'filtered_df' not in st.session_state:
                    st.session_state.filtered_df = filtered_df
                st.session_state.show_results = True  # Show partial results
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            if status == "error":
                # Fallback to basic response with filtered data
                basic_response = (
                    f"I found **{len(filtered_df):,} cases** matching your query, but encountered an error during statistical analysis: {result}. "
                    f"Results below show the filtered cases."
                )
                finalize_assistant_message(
                    basic_response,
                    metadata={
                        "error": str(result),
                        "filters": filters,
                        "method": method,
                        "confidence": confidence
                    }
                )
                # Store filtered data for results display
                st.session_state.last_filters = filters
                st.session_state.last_query_text = query
                st.session_state.last_query_source = "chat"
                st.session_state.filtered_df = filtered_df
                st.session_state.show_results = True  # Show filtered results even if stats failed
                status_box.empty()
                st.session_state.run_in_progress = False
                st.rerun()
                return
            
            # Success - we have full results (CHUNK 6.5)
            final_answer = result.get("response", "⚠️ No summary generated.")
            final_answer += "\n\n📊 Full analysis generated below."
            
            # Replace thinking bubble with final answer
            finalize_assistant_message(final_answer, metadata=result)
            
            # CHUNK 6.5: Update memory state from conversational engine
            if "memory" in result:
                st.session_state.memory_state = result["memory"]
            elif "memory_state" in st.session_state:
                # Memory was already updated by process_conversational_query internally
                pass
            
            # CHUNK 6.7: Store quick_results for debug panel
            if "quick_results" in result:
                st.session_state.last_quick_results = result["quick_results"]
            
            # Store results for display (FULL MODE triggers results)
            st.session_state.last_filters = result.get("filters", filters)
            st.session_state.last_query_text = query
            st.session_state.last_query_source = "chat"
            st.session_state.filtered_df = result.get("filtered_df", filtered_df)
            st.session_state.show_results = True  # FULL MODE shows results
            
            # CHUNK 6.13: Generate SAR if requested
            if is_sar_request:
                try:
                    from src.ai.sar_generator import SARGenerator
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating Safety Assessment Report", status_box)
                    
                    # Get heavy trend alerts for SAR
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for SAR
                    sar_gen = SARGenerator()
                    signals = alerts_result.get("emerging_signals", [])
                    rpf_ranked = alerts_result.get("rpf_ranked", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df)
                    }
                    
                    # Build payload
                    payload = sar_gen.build_sar_payload(
                        alerts=alerts_result,
                        signals=signals,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta
                    )
                    
                    # Generate SAR (heavy mode)
                    sar_content = sar_gen.generate_sar(payload, heavy=True)
                    
                    if sar_content:
                        # Store in session state
                        st.session_state["sar_report"] = {
                            "content": sar_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "payload": payload
                        }
                        # Update assistant message to mention SAR
                        final_answer += "\n\n📄 **Safety Assessment Report (SAR) generated!** View it in the 'SAR Report' tab below."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    # If SAR generation fails, continue without it
                    st.warning(f"⚠️ SAR generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.14: Generate DSUR if requested
            elif is_dsur_request:
                try:
                    from src.ai.dsur_pbrer_generator import DSURPBRERGenerator
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating DSUR Report", status_box)
                    
                    # Get heavy trend alerts for DSUR
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for DSUR
                    gen = DSURPBRERGenerator()
                    signals = alerts_result.get("emerging_signals", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df),
                        "period": "Annual"  # Default, can be customized
                    }
                    
                    # Build payload
                    payload = gen.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta
                    )
                    
                    # Generate DSUR (heavy mode)
                    dsur_content = gen.generate_dsur(payload, heavy=True)
                    
                    if dsur_content:
                        # Store in session state
                        st.session_state["dsur_report"] = {
                            "content": dsur_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "payload": payload
                        }
                        # Update assistant message
                        final_answer += "\n\n📘 **Development Safety Update Report (DSUR) generated!** View it in the 'DSUR / PBRER' tab below."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ DSUR generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.14: Generate PBRER if requested
            elif is_pbrer_request:
                try:
                    from src.ai.dsur_pbrer_generator import DSURPBRERGenerator
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating PBRER Report", status_box)
                    
                    # Get heavy trend alerts for PBRER
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for PBRER
                    gen = DSURPBRERGenerator()
                    signals = alerts_result.get("emerging_signals", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df),
                        "period": "Periodic"  # Default, can be customized
                    }
                    
                    # Build payload
                    payload = gen.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta
                    )
                    
                    # Generate PBRER (heavy mode)
                    pbrer_content = gen.generate_pbrer(payload, heavy=True)
                    
                    if pbrer_content:
                        # Store in session state
                        st.session_state["pbrer_report"] = {
                            "content": pbrer_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "payload": payload
                        }
                        # Update assistant message
                        final_answer += "\n\n📙 **Periodic Benefit-Risk Evaluation Report (PBRER) generated!** View it in the 'DSUR / PBRER' tab below."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ PBRER generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.15: Generate CAPA recommendations if requested
            elif is_capa_request:
                try:
                    from src.ai.capa_recommendations import CAPAEngine
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating CAPA Recommendations", status_box)
                    
                    # Get heavy trend alerts for CAPA
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for CAPA
                    capa_engine = CAPAEngine()
                    signals = alerts_result.get("emerging_signals", [])
                    rpf_ranked = alerts_result.get("rpf_ranked", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df)
                    }
                    
                    # Build payload
                    payload = capa_engine.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        rpf_ranked=rpf_ranked,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta
                    )
                    
                    # Generate CAPA (heavy mode)
                    capa_content = capa_engine.generate_capa(payload, heavy=True)
                    
                    if capa_content:
                        # Store in session state
                        st.session_state["capa_recommendations"] = {
                            "content": capa_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "payload": payload,
                            "priority_signals": rpf_ranked[:5] if rpf_ranked else []
                        }
                        # Update assistant message
                        final_answer += "\n\n🛠️ **CAPA Recommendations generated!** View them in the 'CAPA' tab below."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ CAPA generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.16: Generate Inspection Readiness package if requested
            elif is_inspection_request:
                try:
                    from src.ai.inspection_readiness_engine import InspectionReadinessEngine
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    from src.audit_trail import read_audit_log
                    
                    heartbeat("Generating Inspection Readiness Package", status_box)
                    
                    # Determine agency from query
                    agency = "FDA"
                    if "ema" in query_lower:
                        agency = "EMA"
                    elif "mhra" in query_lower:
                        agency = "MHRA"
                    elif "pmda" in query_lower:
                        agency = "PMDA"
                    
                    # Get heavy trend alerts for inspection package
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for inspection package
                    inspection_engine = InspectionReadinessEngine()
                    signals = alerts_result.get("emerging_signals", [])
                    rpf_ranked = alerts_result.get("rpf_ranked", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Get CAPA data if available
                    capa_data = st.session_state.get("capa_recommendations")
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df)
                    }
                    
                    # Build payload
                    payload = inspection_engine.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        rpf_ranked=rpf_ranked,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta,
                        capa_data=capa_data
                    )
                    
                    # Get audit trail
                    try:
                        audit_trail = read_audit_log(limit=100)
                    except Exception:
                        audit_trail = []
                    
                    # Generate evidence pack (heavy mode)
                    evidence_pack = inspection_engine.generate_evidence_pack(payload, audit_trail, heavy=True)
                    
                    # Generate inspector questions
                    inspector_questions = inspection_engine.generate_inspector_questions(
                        {"signals": signals, "rpf_ranked": rpf_ranked},
                        agency=agency
                    )
                    
                    if evidence_pack:
                        # Store in session state
                        st.session_state["inspection_readiness"] = {
                            "evidence_pack": evidence_pack,
                            "inspector_questions": inspector_questions or "",
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "agency": agency,
                            "payload": payload
                        }
                        # Update assistant message
                        final_answer += f"\n\n📑 **Inspection Readiness Package generated!** View it in the 'Inspection' tab below."
                        if inspector_questions:
                            final_answer += f" Includes simulated {agency} inspector questions for preparation."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ Inspection readiness generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.18: Generate Core Safety Profile (CSP) if requested
            elif is_csp_request:
                try:
                    from src.ai.csp_generator import CSPGenerator
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating Core Safety Profile (CSP)", status_box)
                    
                    # Get heavy trend alerts for CSP
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for CSP
                    csp_engine = CSPGenerator()
                    signals = alerts_result.get("emerging_signals", [])
                    rpf_ranked = alerts_result.get("rpf_ranked", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Get benefit-risk data if available
                    benefit_risk = st.session_state.get("benefit_risk_assessment")
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df)
                    }
                    
                    # Build payload
                    payload = csp_engine.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        rpf_ranked=rpf_ranked,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta,
                        benefit_risk=benefit_risk
                    )
                    
                    # Generate CSP (heavy mode)
                    csp_content = csp_engine.generate_csp(payload, heavy=True)
                    
                    if csp_content:
                        # Determine version (increment if CSP exists)
                        existing_csp = st.session_state.get("csp_profile")
                        version = "1.0"
                        if existing_csp:
                            try:
                                prev_version = float(existing_csp.get("version", "1.0"))
                                version = f"{prev_version + 0.1:.1f}"
                            except Exception:
                                version = "1.0"
                        
                        # Store in session state
                        st.session_state["csp_profile"] = {
                            "content": csp_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "version": version,
                            "payload": payload
                        }
                        # Update assistant message
                        final_answer += f"\n\n🧬 **Core Safety Profile (CSP) generated!** Version {version}. View it in the 'CSP' tab below."
                        final_answer += "\n\nThe CSP includes Important Identified Risks, Important Potential Risks, Missing Information, and recommended CCDS wording aligned with EMA RMP Annex 1."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ CSP generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # CHUNK 6.19: Generate Label Impact Assessment if requested
            elif is_label_impact_request:
                try:
                    from src.ai.label_impact_engine import LabelImpactEngine
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    heartbeat("Generating Label Impact Assessment", status_box)
                    
                    # Get heavy trend alerts for label impact
                    alerts_result = detect_trend_alerts_heavy(normalized_df)
                    
                    # Extract data for label impact
                    label_engine = LabelImpactEngine()
                    signals = alerts_result.get("emerging_signals", [])
                    rpf_ranked = alerts_result.get("rpf_ranked", [])
                    
                    # Collect subgroup and lot data
                    subgroups = {}
                    lot_findings = []
                    narrative_highlights = []
                    
                    for alert in alerts_result.get("alerts", []):
                        if alert.get("subgroups"):
                            subgroups.update(alert.get("subgroups", {}))
                        if alert.get("lot_alerts"):
                            lot_findings.extend(alert.get("lot_alerts", []))
                        if alert.get("narrative_clusters"):
                            narrative_highlights.extend(alert.get("narrative_clusters", []))
                    
                    # Get CSP and benefit-risk data if available
                    csp_data = st.session_state.get("csp_profile")
                    benefit_risk = st.session_state.get("benefit_risk_assessment")
                    
                    # Build metadata
                    meta = {
                        "drug": filters.get("drug", "Multiple Drugs") if isinstance(filters.get("drug"), str) else (filters.get("drug", ["Multiple Drugs"])[0] if filters.get("drug") else "Multiple Drugs"),
                        "reaction": filters.get("reaction", "Multiple Reactions") if isinstance(filters.get("reaction"), str) else (filters.get("reaction", ["Multiple Reactions"])[0] if filters.get("reaction") else "Multiple Reactions"),
                        "total_cases": len(normalized_df)
                    }
                    
                    # Build payload
                    payload = label_engine.build_payload(
                        alerts=alerts_result,
                        signals=signals,
                        csp=csp_data,
                        rpf_ranked=rpf_ranked,
                        subgroups=subgroups if subgroups else None,
                        lot_findings=lot_findings if lot_findings else None,
                        narrative_highlights=narrative_highlights if narrative_highlights else None,
                        meta=meta,
                        benefit_risk=benefit_risk
                    )
                    
                    # Generate label impact assessment (heavy mode)
                    label_content = label_engine.generate_label_impact(payload, heavy=True)
                    
                    if label_content:
                        # Determine impact level from content (simple heuristic)
                        impact_level = "Not Assessed"
                        if "High Impact" in label_content:
                            impact_level = "High Impact"
                        elif "Medium Impact" in label_content:
                            impact_level = "Medium Impact"
                        elif "Low Impact" in label_content:
                            impact_level = "Low Impact"
                        elif "No Impact" in label_content or "insufficient" in label_content.lower():
                            impact_level = "No Impact"
                        
                        # Store in session state
                        st.session_state["label_impact_assessment"] = {
                            "content": label_content,
                            "meta": meta,
                            "generated_on": datetime.now().isoformat(),
                            "impact_level": impact_level,
                            "payload": payload
                        }
                        # Update assistant message
                        final_answer += f"\n\n📄 **Label Impact Assessment generated!** Impact Level: {impact_level}. View it in the 'Label Impact' tab below."
                        final_answer += "\n\nThe assessment includes proposed EMA SmPC and FDA USPI changes, CCDS updates, regulatory justification, and reviewer notes for QPPV & Safety Review Committee."
                        finalize_assistant_message(final_answer, metadata=result)
                except Exception as e:
                    st.warning(f"⚠️ Label Impact Assessment generation encountered an issue: {str(e)}. Full analysis results are still available.")
            
            # Save to query history
            history = st.session_state.get("query_history", [])
            history.append({
                "query_text": query,
                "timestamp": datetime.now().isoformat(),
                "source": "chat_full",
            })
            st.session_state.query_history = history[-10:]
            
            status_box.empty()
            
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)[:200]}"
            finalize_assistant_message(error_msg, metadata={"error": str(e)})
            if 'status_box' in locals():
                status_box.empty()
            st.error(error_msg)
        finally:
            st.session_state.run_in_progress = False
        
        st.rerun()
    
    # ============================================================
    # ENTERPRISE BLUE LAYOUT - CHUNK 3A/3C
    # ============================================================
    
    # Load enterprise blue theme
    from src.styles import load_modern_blue_styles
    load_modern_blue_styles()
    
    # ============================================================
    # 1. 🧠 SMART SUGGESTIONS PANEL (Unified Recommendations - CHUNK 6.9)
    # ============================================================
    st.markdown("<div class='as-card'>", unsafe_allow_html=True)
    
    # Add button to trigger full analysis from current query
    if st.button("📊 Generate Full Safety Analysis", use_container_width=True, type="primary"):
        # If we have a last query, trigger full analysis for it
        last_query = st.session_state.get("last_query_text")
        if last_query and data_available:
            # Switch to full mode temporarily
            old_mode = st.session_state.get("analysis_mode", "fast")
            st.session_state.analysis_mode = "full"
            # Re-run the last query in full mode
            on_send(last_query)
        else:
            st.info("💡 Send a query first, then click this button to generate a full analysis with detailed statistics.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 3. ⚡ MODE SWITCH (FAST vs FULL) - Informational
    # ============================================================
    st.markdown("<div class='as-card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    # Get current mode
    current_mode = st.session_state.get("analysis_mode", "fast")
    
    with col1:
        if st.button("⚡ Fast Exploration Mode", use_container_width=True,
                     type="primary" if current_mode == "fast" else "secondary"):
            st.session_state.analysis_mode = "fast"
            st.success("✅ Fast mode enabled — no heavy computation.")
            st.rerun()
    
    with col2:
        if st.button("📊 Full Analysis Mode", use_container_width=True,
                     type="primary" if current_mode == "full" else "secondary"):
            st.session_state.analysis_mode = "full"
            st.success("✅ Full analysis mode enabled — next message will run full pipeline.")
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 3. 🧠 SMART SUGGESTIONS PANEL (Unified Recommendations - CHUNK 6.9)
    # ============================================================
    st.markdown("<div class='as-card'>", unsafe_allow_html=True)
    
    # CHUNK 6.9: Use new Enterprise Suggestions Panel
    from src.ui.suggestions_panel import render_suggestions_panel
    
    # Get data for suggestions panel
    starter_questions, top_drugs, top_reactions, all_drugs, all_reactions = _build_dynamic_starter_questions(
        normalized_df
    )
    
    # Get recent queries
    recent_queries = st.session_state.get("query_history", [])
    
    # Get saved queries
    saved_queries = st.session_state.get("saved_queries", [])
    
    # Render new enterprise suggestions panel
    render_suggestions_panel(
        top_drugs=top_drugs,
        top_reactions=top_reactions,
        starter_questions=starter_questions,
        recent_queries=recent_queries,
        saved_queries=saved_queries if saved_queries else None,
        on_select=None  # Auto-fill handled by JavaScript in suggestions_panel.py
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 4. 📊 QUICK STATS PANEL (CHUNK 6.10 - Pre-Chat Mini Insights)
    # ============================================================
    if data_available:
        from src.ui.quickstats_panel import render_quickstats
        st.markdown("<div class='as-card'>", unsafe_allow_html=True)
        render_quickstats(normalized_df)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 5. 📬 CHAT INTERFACE (After QuickStats - CHUNK 6.10)
    # ============================================================
    st.markdown("### 💬 Natural Language Assistant")
    
    with st.container():
        st.markdown("<div class='as-card'>", unsafe_allow_html=True)
        render_chat_interface(on_send_callback=on_send)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 6. 🛠 SETTINGS (Search Enhancers)
    # ============================================================
    st.markdown("<div class='as-card'>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.session_state.use_smart_search = st.checkbox(
            "⚙️ Smart Search Enhancements",
            value=st.session_state.get("use_smart_search", True)
        )
    
    with col_b:
        st.session_state.enable_ai_enhanced = st.checkbox(
            "🤖 AI-Enhanced Interpretation",
            value=st.session_state.get("enable_ai_enhanced", False),
            help=(
                "⚠️ Privacy Notice: When enabled, AI features include enhanced query interpretation, "
                "conversational summaries, and intelligent insights. Query metadata (filters, not raw data) "
                "may be sent to OpenAI/Groq APIs for processing."
            )
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # 7. 🧠 MEMORY INSPECTOR PANEL (CHUNK 6.7 - Debug Mode Only)
    # ============================================================
    if st.session_state.get("debug_mode", False):
        st.markdown("<div class='as-card'>", unsafe_allow_html=True)
        
        with st.expander("🧠 Conversation Memory (Debug Mode)", expanded=False):
            st.markdown("#### Memory State")
            memory_state = st.session_state.get("memory_state", {})
            st.json(memory_state)
            
            st.markdown("#### Last 5 Chat Messages")
            chat_history = st.session_state.get("chat_history", [])
            recent_msgs = chat_history[-5:] if len(chat_history) > 5 else chat_history
            if recent_msgs:
                # Convert to JSON-serializable format
                json_msgs = []
                for msg in recent_msgs:
                    json_msg = {
                        "role": msg.get("role", "unknown"),
                        "content": msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", ""),
                        "status": msg.get("status", "complete"),
                        "timestamp": str(msg.get("timestamp")) if msg.get("timestamp") else None
                    }
                    json_msgs.append(json_msg)
                st.json(json_msgs)
            else:
                st.info("No chat messages yet.")
            
            st.markdown("#### Quick Follow-Up Insights")
            last_quick = st.session_state.get("last_quick_results", None)
            if last_quick:
                st.json(last_quick)
            else:
                st.info("No quick results yet. Send a message to generate insights.")
            
            st.markdown("#### Last Filters Applied")
            filters = memory_state.get("filters", {})
            if filters:
                st.json(filters)
            else:
                st.info("No filters applied yet.")
            
            st.markdown("#### Extracted Entities")
            col1, col2 = st.columns(2)
            with col1:
                drug = memory_state.get("drug")
                if drug:
                    st.metric("Drug", drug)
                else:
                    st.caption("Drug: Not detected")
                
                reactions = memory_state.get("reactions", [])
                if reactions:
                    st.markdown(f"**Reactions ({len(reactions)}):**")
                    for r in reactions[:5]:
                        st.caption(f"  • {r}")
                    if len(reactions) > 5:
                        st.caption(f"  ... and {len(reactions) - 5} more")
                else:
                    st.caption("Reactions: None detected")
            
            with col2:
                time_window = memory_state.get("time_window")
                if time_window:
                    st.metric("Time Window", time_window)
                else:
                    st.caption("Time Window: Not specified")
                
                goals = memory_state.get("user_goals", [])
                if goals:
                    st.markdown(f"**User Goals ({len(goals)}):**")
                    for g in goals:
                        st.caption(f"  • {g}")
                else:
                    st.caption("Goals: None detected")
            
            st.markdown("#### Raw Conversation Summary")
            summary = memory_state.get("conversation_summary", "")
            if summary:
                st.text_area(
                    "Summary (last 500 chars)",
                    value=summary[-500:] if len(summary) > 500 else summary,
                    height=150,
                    disabled=True,
                    key="debug_summary_display"
                )
                st.caption(f"Total length: {len(summary)} characters")
            else:
                st.info("Conversation summary is empty.")
            
            st.markdown("---")
            st.caption("💡 This panel helps debug memory extraction and follow-up logic.")
            st.caption("💡 Enable/disable debug mode in the sidebar under Developer Tools.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_nl_query_tab_OLD(normalized_df):
    """Step 2 – natural-language query workbench (OLD VERSION - KEPT FOR REFERENCE)."""

    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    starter_questions, top_drugs, top_reactions, all_drugs, all_reactions = _build_dynamic_starter_questions(
        normalized_df
    )

    # OPTIMIZED HORIZONTAL LAYOUT: Better use of screen real estate
    # Row 1: Starter Questions | Top Drugs | Top Reactions (3 columns)
    st.markdown("### ⚡ Quick Access")
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    
    with row1_col1:
        st.markdown("**⚡ Starter Questions**")
        if starter_questions:
            for idx, (title, query, icon) in enumerate(starter_questions[:4]):  # Limit to 4 to fit
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

    with row1_col2:
        st.markdown("**💊 Top Drugs**")
        if top_drugs:
            for idx, drug in enumerate(top_drugs[:4]):  # Limit to 4
                if st.button(
                    drug,
                    key=f"drug_chip_{idx}",
                    use_container_width=True,
                ):
                    current = st.session_state.get("query_text", "")
                    drug_lower = drug.lower()
                    current_lower = current.lower()
                    if drug_lower in current_lower and f"drug {drug_lower}" in current_lower:
                        st.info(f"ℹ️ '{drug}' is already in your query")
                    else:
                        new_q = (
                            f"{current} drug {drug}".strip()
                            if current
                            else f"Show cases with drug {drug}"
                        )
                        st.session_state.query_text = new_q
                        st.rerun()
            
            # Browse all drugs (collapsible)
            if all_drugs and len(all_drugs) > 4:
                with st.expander(f"🔍 All drugs ({len(all_drugs)})", expanded=False):
                    selected_drugs = st.multiselect(
                        "Select drug(s)",
                        options=all_drugs,
                        default=[],
                        key="browse_all_drugs",
                        help="Select drugs to add to query",
                    )
                    if selected_drugs:
                        current = st.session_state.get("query_text", "")
                        current_lower = current.lower()
                        new_drugs = [d for d in selected_drugs if d.lower() not in current_lower]
                        if new_drugs:
                            drug_terms = " OR ".join([f"drug {d}" for d in new_drugs])
                            new_q = f"{current} OR {drug_terms}".strip() if current else f"Show cases with {drug_terms}"
                            st.session_state.query_text = new_q
                            st.rerun()
                        else:
                            st.caption("No drug data available.")
        
    with row1_col3:
        st.markdown("**⚠️ Top Reactions**")
        if top_reactions:
            for idx, reaction in enumerate(top_reactions[:4]):  # Limit to 4
                if st.button(
                    reaction,
                    key=f"reaction_chip_{idx}",
                    use_container_width=True,
                ):
                    current = st.session_state.get("query_text", "")
                    reaction_lower = reaction.lower()
                    current_lower = current.lower()
                    if reaction_lower in current_lower and f"reaction {reaction_lower}" in current_lower:
                        st.info(f"ℹ️ '{reaction}' is already in your query")
                    else:
                        has_reaction = "reaction" in current_lower
                        if has_reaction:
                            new_q = f"{current} OR reaction {reaction}".strip() if current else f"Show cases with reaction {reaction}"
                        else:
                            new_q = f"{current} reaction {reaction}".strip() if current else f"Show cases with reaction {reaction}"
                        st.session_state.query_text = new_q
                        st.rerun()
            
            # Browse all reactions (collapsible)
            if all_reactions and len(all_reactions) > 4:
                with st.expander(f"🔍 All reactions ({len(all_reactions)})", expanded=False):
                    selected_reactions = st.multiselect(
                        "Select reaction(s)",
                        options=all_reactions,
                        default=[],
                        key="browse_all_reactions",
                        help="Select reactions to add to query",
                    )
                    if selected_reactions:
                        current = st.session_state.get("query_text", "")
                        current_lower = current.lower()
                        new_reactions = [r for r in selected_reactions if r.lower() not in current_lower]
                        if new_reactions:
                            reaction_terms = " OR ".join([f"reaction {r}" for r in new_reactions])
                            has_reaction = "reaction" in current_lower
                            if has_reaction:
                                new_q = f"{current} OR {reaction_terms}".strip()
                            else:
                                new_q = f"{current} {reaction_terms}".strip() if current else f"Show cases with {reaction_terms}"
                            st.session_state.query_text = new_q
                            st.rerun()
                        else:
                            st.caption("No reaction data available.")

        st.markdown("---")
    
    # Row 2: Saved Queries | Recent Queries (2 columns)
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.markdown("**📁 Saved Queries**")
        saved_queries = st.session_state.get("saved_queries", [])
        if saved_queries:
            for i, sq in enumerate(saved_queries[:5]):  # Limit to 5
                label = f"▶ {sq['name']}"
                if st.button(label, key=f"run_saved_{i}", use_container_width=True):
                    st.session_state.query_text = sq["query_text"]
                    st.session_state.last_query_text = sq["query_text"]
                    st.session_state.last_filters = sq["filters"]
                    st.session_state.last_query_source = "saved"
                    st.session_state.show_results = True
                    st.rerun()

            # Save current query (compact)
            with st.expander("💾 Save Current Query", expanded=False):
                save_name = st.text_input(
                    "Query name",
                    key="save_query_name",
                    placeholder="e.g., Semaglutide pancreatitis 2024",
                )
                can_save = bool(
                    st.session_state.get("last_filters")
                    and st.session_state.get("last_query_text")
                )
                if st.button("💾 Save", key="save_query_button", use_container_width=True, disabled=not can_save):
                    name = save_name.strip() or f"Query {datetime.now():%Y-%m-%d %H:%M}"
                    saved = st.session_state.get("saved_queries", [])
                    if any(sq["name"] == name for sq in saved):
                        st.warning("Query name already exists.")
                    else:
                        saved.append({
                            "name": name,
                            "query_text": st.session_state.get("last_query_text", ""),
                            "filters": st.session_state.get("last_filters", {}),
                        })
                        st.session_state.saved_queries = saved[-15:]
                        st.success(f"✅ Saved: {name}")
                        st.rerun()
        else:
            st.caption("No saved queries yet.")
            # Allow saving even if no saved queries exist
            with st.expander("💾 Save Current Query", expanded=False):
                save_name = st.text_input(
                    "Query name",
                    key="save_query_name",
                    placeholder="e.g., Semaglutide pancreatitis 2024",
                )
                can_save = bool(
                    st.session_state.get("last_filters")
                    and st.session_state.get("last_query_text")
                )
                if st.button("💾 Save", key="save_query_button", use_container_width=True, disabled=not can_save):
                    name = save_name.strip() or f"Query {datetime.now():%Y-%m-%d %H:%M}"
                    saved = st.session_state.get("saved_queries", [])
                    saved.append({
                        "name": name,
                        "query_text": st.session_state.get("last_query_text", ""),
                        "filters": st.session_state.get("last_filters", {}),
                    })
                    st.session_state.saved_queries = saved[-15:]
                    st.success(f"✅ Saved: {name}")
                    st.rerun()
            
    with row2_col2:
        st.markdown("**🕒 Recent Queries**")
        history = st.session_state.get("query_history", [])
        if history:
            # Show last 5 queries (most recent first)
            for entry in reversed(history[-5:]):
                query_text_display = entry.get("query_text", "")[:50] + "..." if len(entry.get("query_text", "")) > 50 else entry.get("query_text", "")
                if st.button(
                    f"▶ {query_text_display}",
                    key=f"recent_{hash(entry.get('query_text', ''))}",
                    use_container_width=True,
                    help=entry.get("query_text", ""),
                ):
                    st.session_state.query_text = entry["query_text"]
                    st.session_state.last_query_text = entry["query_text"]
                    st.session_state.show_results = False
                    st.rerun()
        else:
            st.caption("No recent queries.")
    
            st.markdown("---")
    
    # Row 3: Main Query Input Section (full width)
    st.markdown("### 💬 Ask a question")
    st.caption("Type a question in plain English, or use the options above.")

    # Checkboxes in a row above the query input
    checkbox_col1, checkbox_col2 = st.columns([1, 1])
    with checkbox_col1:
        smart_search = st.checkbox(
            "✨ Smart search (typo correction + suggestions)",
            value=False,
            help="Correct likely typos for drugs/reactions and suggest alternatives.",
        )
    with checkbox_col2:
        use_llm = st.checkbox(
            "🤖 AI-enhanced",
            value=st.session_state.get("use_llm", False),
            key="use_llm_checkbox",
            help=(
                "⚠️ Privacy Notice: When enabled, AI features include enhanced query interpretation, "
                "literature summarization, and case narrative analysis. Query text may be sent to external AI services."
            )
        )
        st.session_state.use_llm = use_llm

    # Main query input (full width)
    st.markdown("""
    <div style='margin-bottom: 0.5rem;'>
        <label style='font-size: 0.9rem; font-weight: 600; color: #1e293b; display: block; margin-bottom: 0.4rem;'>
            Enter safety question
        </label>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="query-textarea-wrapper">', unsafe_allow_html=True)
    query_text = st.text_area(
        "Query input",
        value=st.session_state.get(
            "query_text", st.session_state.get("last_query_text", "")
        ),
        height=100,
        key="query_input",
        label_visibility="collapsed",
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
            pass
    
    run_query_enabled = (
        st.session_state.data is not None
        and st.session_state.normalized_data is not None
    )
    
    # Run query button (centered, prominent)
    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
    with button_col2:
        run_query = st.button(
            "🚀 Run query",
            type="primary",
            use_container_width=True,
            disabled=not run_query_enabled,
            key="run_main_query",
        )

    if not run_query_enabled and query_text:
        st.info("ℹ️ Upload and load data first to run queries.")

    if run_query and query_text and run_query_enabled:
        with st.spinner("🔎 Interpreting your query…"):
            import signal
            import time
            
            working_query = query_text
            applied_corrections: Optional[Dict[str, tuple]] = None
            
            start_time = time.time()
            timeout_seconds = 30  # 30 second timeout

            try:
                # Smart typo correction (auto-apply when confident) - with timeout check
                if smart_search and normalized_df is not None:
                    if time.time() - start_time < timeout_seconds:
                        suggestions = suggest_query_corrections(working_query, normalized_df)
                        if suggestions:
                            corrected = get_corrected_query(working_query, suggestions)
                            applied_corrections = suggestions
                            # Only show suggestion if it's different from the original
                            if corrected.strip().lower() != working_query.strip().lower():
                                working_query = corrected
                                st.info(f"Did you mean: **{corrected}**")
                                st.session_state.last_query_corrections = suggestions
                            else:
                                # Correction resulted in same query - don't show or apply
                                applied_corrections = None
                        else:
                            st.warning("⏱️ Query correction timed out, skipping...")

                # Use hybrid router (rule-based first, LLM fallback if enabled) - with timeout check
                if time.time() - start_time < timeout_seconds:
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
                else:
                    st.error("⏱️ Query interpretation timed out (30 seconds). Please try a simpler query or disable smart search.")
                    filters = {}
                
                is_valid, error_msg = nl_query_parser.validate_filters(filters)
                
            except Exception as e:
                st.error(f"❌ Error interpreting query: {str(e)[:200]}")
                filters = {}
                is_valid = False
                error_msg = "Query interpretation failed. Please try rephrasing your question."

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
                    st.info(f"Applying fallback: {fallback_filters}")
            
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
