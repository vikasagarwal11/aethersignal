"""
Query interface component for AetherSignal.
Enterprise-grade natural language query interface with Starter Questions, Smart Snippets, and professional layout.
"""

from datetime import datetime
import re
import streamlit as st

from src import nl_query_parser
from src import watchlist_tab


def render_nl_query_tab(normalized_df):
    """Enterprise-grade Natural Language Query Interface - Fortune-50 Pharma Standard."""
    
    # Hero Section
    st.markdown("""
    <div class="quantum-query-hero">
        <h2 style="margin: 0; color: white; font-size: 2rem; font-weight: 700;">🔍 Ask Anything About Your Safety Data</h2>
        <p style="color: #e0e7ff; font-size: 1.1rem; margin: 0.8rem 0 0 0; opacity: 0.9;">
            Type in plain English • Get instant results • Powered by quantum-inspired ranking
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout: Left (Saved Queries) | Center (Main Query) | Right (History)
    main_col1, main_col2, main_col3 = st.columns([1, 2.5, 1])
    
    with main_col1:
        # SECTION E: Saved Queries (Left Side, Collapsible)
        st.markdown("#### 📁 Saved Queries")
        saved_queries = st.session_state.get("saved_queries", [])
        
        if saved_queries:
            with st.expander("View saved queries", expanded=False):
                for i, sq in enumerate(saved_queries):
                    col_name, col_actions = st.columns([2, 1])
                    with col_name:
                        st.markdown(f"**{sq['name']}**")
                    with col_actions:
                        if st.button("▶", key=f"run_saved_{i}", help="Run query"):
                            st.session_state.query_text = sq["query_text"]
                            st.session_state.last_query_text = sq["query_text"]
                            st.session_state.last_filters = sq["filters"]
                            st.session_state.last_query_source = "saved"
                            st.session_state.show_results = True
                            st.rerun()
        
        # Save current query
        st.markdown("---")
        save_name = st.text_input("Name current query", key="save_query_name", placeholder="e.g., Semaglutide Pancreatitis 2024")
        can_save = bool(st.session_state.get("last_filters") and st.session_state.get("last_query_text"))
        if st.button("💾 Save Query", key="save_query_button", use_container_width=True, disabled=not can_save):
            if not save_name.strip():
                # Auto-generate name
                save_name = f"Query from {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                save_name = save_name.strip()
            
            saved_queries = st.session_state.get("saved_queries", [])
            if any(sq["name"] == save_name for sq in saved_queries):
                st.warning("A saved query with that name already exists.")
            else:
                saved_queries.append({
                    "name": save_name,
                    "query_text": st.session_state.get("last_query_text", ""),
                    "filters": st.session_state.get("last_filters", {}),
                })
                st.session_state.saved_queries = saved_queries[-15:]  # Keep last 15
                st.success(f"✅ Saved: '{save_name}'")
                st.rerun()
    
    with main_col2:
        # SECTION A: Starter Questions (Tiles)
        st.markdown("### ⚡ Starter Questions")
        st.caption("Click any tile to fill the query box with a complete example")
        
        # Generate fully dynamic starter questions based on actual data (NO hardcoded values)
        starter_questions = []
        
        if normalized_df is not None and len(normalized_df) > 0:
            # Extract data-driven values from uploaded dataset
            top_drug = None
            top_reaction = None
            most_recent_year = None
            oldest_year = None
            age_percentiles = None
            has_serious = False
            has_fatal = False
            has_country = False
            
            # Get top drug (handle semicolon-separated values)
            if "drug_name" in normalized_df.columns:
                drug_series = normalized_df["drug_name"].str.split("; ").explode()
                top_drug = drug_series.value_counts().head(1).index[0] if len(drug_series) > 0 else None
            
            # Get top reaction (handle semicolon-separated values)
            if "reaction" in normalized_df.columns:
                reaction_series = normalized_df["reaction"].str.split("; ").explode()
                top_reaction = reaction_series.value_counts().head(1).index[0] if len(reaction_series) > 0 else None
            
            # Extract dates from dataset (for dynamic year references)
            date_columns = ["report_date", "receive_date", "event_date", "onset_date"]
            date_col = None
            for col in date_columns:
                if col in normalized_df.columns:
                    date_col = col
                    break
            
            if date_col:
                try:
                    from src.utils import parse_date
                    # Try to extract years from date column
                    dates = normalized_df[date_col].dropna()
                    years = []
                    for date_val in dates.head(1000):  # Sample first 1000 for speed
                        try:
                            parsed = parse_date(str(date_val))
                            if parsed:
                                years.append(parsed.year)
                        except:
                            pass
                        # Also try direct year extraction (YYYY format)
                        if isinstance(date_val, str) and len(date_val) >= 4:
                            year_match = re.search(r'\b(19|20)\d{2}\b', str(date_val))
                            if year_match:
                                years.append(int(year_match.group(0)))
                    
                    if years:
                        most_recent_year = max(years)
                        oldest_year = min(years)
                        # Use year that's 2-3 years before most recent for "since" queries
                        years_ago = max(2, min(3, most_recent_year - oldest_year))
                        comparison_year = most_recent_year - years_ago
                except:
                    pass
            
            # Extract age statistics from dataset (for dynamic age ranges)
            elderly_threshold = None
            pediatric_age = None
            if "age" in normalized_df.columns:
                try:
                    from src.utils import extract_age
                    ages = normalized_df["age"].apply(extract_age).dropna()
                    if len(ages) > 0:
                        age_percentiles = {
                            "p75": int(ages.quantile(0.75)) if len(ages) > 0 else None,
                            "p25": int(ages.quantile(0.25)) if len(ages) > 0 else None,
                            "min": int(ages.min()) if len(ages) > 0 else None,
                            "max": int(ages.max()) if len(ages) > 0 else None,
                        }
                        # Use 75th percentile as "elderly" threshold if reasonable (>50), else use 65
                        elderly_threshold = age_percentiles.get("p75") if (age_percentiles.get("p75") and age_percentiles.get("p75") > 50) else 65
                        # Use 25th percentile or 18 for pediatric threshold
                        pediatric_age = min(18, age_percentiles.get("p25", 18)) if age_percentiles.get("p25") else 18
                except:
                    age_percentiles = None
                    elderly_threshold = 65  # Fallback
                    pediatric_age = 18  # Fallback
            
            # Check if serious/fatal/country data exists
            has_serious = "serious" in normalized_df.columns or "seriousness" in normalized_df.columns
            has_fatal = "outcome" in normalized_df.columns or "outc_cod" in normalized_df.columns
            has_country = "country" in normalized_df.columns
            
            # Build fully dynamic starter questions (NO hardcoded values)
            if top_drug and top_reaction:
                questions_list = [
                    ("Serious Cases", f"Show all serious cases with drug {top_drug} and reaction {top_reaction}", "🔴"),
                ]
                
                # Add trending question with dynamic date if available
                if most_recent_year and comparison_year:
                    questions_list.append(("Trending Reactions", f"What reactions increased since {comparison_year} for drug {top_drug}?", "📈"))
                elif top_drug:
                    questions_list.append(("Trending Reactions", f"What are the top reactions for drug {top_drug}?", "📈"))
                
                # Add demographics question with dynamic age if available
                if age_percentiles and elderly_threshold and has_fatal:
                    questions_list.append(("High-Risk Demographics", f"Show serious cases in patients age {elderly_threshold}+ with fatal outcomes", "👴"))
                elif has_serious and has_fatal:
                    questions_list.append(("High-Risk Demographics", "Show serious cases with fatal outcomes", "👴"))
                
                # Add recent reports question with dynamic year if available
                if most_recent_year:
                    questions_list.append(("Recent Reports", f"Show all cases reported in {most_recent_year}", "📅"))
                else:
                    questions_list.append(("Recent Reports", "Show all recent cases", "📅"))
                
                # Add pediatric question with dynamic age if available
                if pediatric_age:
                    questions_list.append(("Pediatric Cases", f"Show all cases in patients under {pediatric_age} years old", "👶"))
                else:
                    questions_list.append(("Pediatric Cases", "Show all pediatric cases", "👶"))
                
                # Add geographic analysis if country data exists
                if has_country:
                    questions_list.append(("Geographic Analysis", "Show cases by country for serious outcomes", "🌍"))
                
                starter_questions = questions_list[:6]  # Show max 6
            else:
                # Generic questions when we have data but no specific drugs/reactions
                starter_questions = [
                    ("Serious Cases", "Show all serious cases by drug and reaction", "🔴"),
                ]
                if most_recent_year and comparison_year:
                    starter_questions.append(("Trending Reactions", f"What reactions increased since {comparison_year}?", "📈"))
                else:
                    starter_questions.append(("Trending Reactions", "What are the top reactions?", "📈"))
                
                if age_percentiles and elderly_threshold:
                    starter_questions.append(("High-Risk Demographics", f"Show serious cases in patients age {elderly_threshold}+ with fatal outcomes", "👴"))
                elif has_serious and has_fatal:
                    starter_questions.append(("High-Risk Demographics", "Show serious cases with fatal outcomes", "👴"))
                
                if most_recent_year:
                    starter_questions.append(("Recent Reports", f"Show all cases reported in {most_recent_year}", "📅"))
                else:
                    starter_questions.append(("Recent Reports", "Show all recent cases", "📅"))
                
                if pediatric_age:
                    starter_questions.append(("Pediatric Cases", f"Show all cases in patients under {pediatric_age} years old", "👶"))
                else:
                    starter_questions.append(("Pediatric Cases", "Show all pediatric cases", "👶"))
                
                if has_country:
                    starter_questions.append(("Geographic Analysis", "Show cases by country for serious outcomes", "🌍"))
        else:
            # Generic questions when no data loaded (these are templates, not hardcoded examples)
            starter_questions = [
                ("Serious Cases", "Show all serious cases by drug and reaction", "🔴"),
                ("Trending Reactions", "What are the top reactions?", "📈"),
                ("Demographics", "Show cases by patient demographics", "👥"),
            ]
        
        # Display tiles in 3 columns
        tile_cols = st.columns(3)
        for idx, (title, query, icon) in enumerate(starter_questions[:6]):  # Show max 6 tiles
            with tile_cols[idx % 3]:
                if st.button(
                    f"{icon}\n\n**{title}**\n\n{query[:40]}...",
                    key=f"starter_{idx}",
                    use_container_width=True,
                    help=query
                ):
                    st.session_state.query_text = query
                    st.rerun()
        
        st.markdown("---")
        
        # SECTION B: Smart Snippets (One-click chips)
        st.markdown("### ⚡ Smart Snippets")
        st.caption("Click any chip to quickly add to your query")
        
        # Generate snippets from actual data
        top_drugs = []
        top_reactions = []
        
        if normalized_df is not None:
            if "drug_name" in normalized_df.columns:
                # Get top drugs, split by semicolon if needed
                drug_series = normalized_df["drug_name"].str.split("; ").explode()
                top_drugs = drug_series.value_counts().head(8).index.tolist()
            if "reaction" in normalized_df.columns:
                # Get top reactions, split by semicolon if needed
                reaction_series = normalized_df["reaction"].str.split("; ").explode()
                top_reactions = reaction_series.value_counts().head(8).index.tolist()
        
        # Display drug chips
        if top_drugs:
            st.markdown("**💊 Most Frequent Drugs**")
            drug_cols = st.columns(4)
            for idx, drug in enumerate(top_drugs[:8]):
                with drug_cols[idx % 4]:
                    if st.button(drug, key=f"drug_chip_{idx}", use_container_width=True, type="primary"):
                        current_query = st.session_state.get("query_text", "")
                        new_query = f"{current_query} drug {drug}".strip() if current_query else f"Show cases with drug {drug}"
                        st.session_state.query_text = new_query
                        st.rerun()
        
        # Display reaction chips
        if top_reactions:
            st.markdown("**⚠️ Top Reactions**")
            reaction_cols = st.columns(4)
            for idx, reaction in enumerate(top_reactions[:8]):
                with reaction_cols[idx % 4]:
                    if st.button(reaction, key=f"reaction_chip_{idx}", use_container_width=True, type="secondary"):
                        current_query = st.session_state.get("query_text", "")
                        new_query = f"{current_query} reaction {reaction}".strip() if current_query else f"Show cases with reaction {reaction}"
                        st.session_state.query_text = new_query
                        st.rerun()
        
        if not top_drugs and not top_reactions:
            st.info("💡 Upload and load data to see smart snippets from your dataset.")
        
        st.markdown("---")
        
        # SECTION C: Enterprise Text Box (Centered, Big)
        st.markdown("### 💬 Enter Your Safety Question")
        
        # Add custom CSS for query text area visibility
        st.markdown("""
        <style>
        /* Make query text area highly visible - target Streamlit's textarea structure */
        div[data-testid="stTextArea"] > div > div > textarea,
        textarea[data-testid="stTextArea"],
        textarea.stTextArea textarea,
        .stTextArea textarea {
            background: white !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            font-size: 1.1rem !important;
            line-height: 1.6 !important;
            color: #1e293b !important;
            font-weight: 400 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
            min-height: 120px !important;
            width: 100% !important;
        }
        
        div[data-testid="stTextArea"] > div > div > textarea:focus,
        textarea[data-testid="stTextArea"]:focus,
        textarea.stTextArea textarea:focus,
        .stTextArea textarea:focus {
            border-color: #2563eb !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3) !important;
            outline: 2px solid rgba(59, 130, 246, 0.2) !important;
            outline-offset: 2px !important;
        }
        
        div[data-testid="stTextArea"] > div > div > textarea::placeholder,
        textarea[data-testid="stTextArea"]::placeholder,
        textarea.stTextArea textarea::placeholder,
        .stTextArea textarea::placeholder {
            color: #94a3b8 !important;
            font-size: 1rem !important;
            opacity: 0.8 !important;
        }
        
        /* Ensure container also has proper styling */
        div[data-testid="stTextArea"] {
            background: transparent !important;
        }
        
        div[data-testid="stTextArea"] > div > div {
            background: transparent !important;
            border: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        query_text = st.text_area(
            "",
            value=st.session_state.get("query_text", st.session_state.get("last_query_text", "")),
            height=120,
            key="query_input",
            label_visibility="collapsed",
            placeholder=(
                "Ask anything about your safety data...\n\n"
                "Examples:\n"
                "• Show serious cases with drug semaglutide and reaction pancreatitis since 2021\n"
                "• Find cases in women age 30-60 with fatal outcomes\n"
                "• Cases with drug X from 2020-01-01 to 2023-12-31"
            ),
            help="Tips: Use 'drug X', 'reaction Y', 'age 18-65', 'serious', 'country US', 'since 2020', 'from 2020-01-01', 'until 2023-12-31'",
        )
        
        # Large Run Button
        run_query_enabled = st.session_state.data is not None and st.session_state.normalized_data is not None
        run_query = st.button(
            "🚀 Run Safety Query",
            type="primary",
            use_container_width=True,
            disabled=not run_query_enabled,
            key="run_main_query"
        )
        
        if not run_query_enabled and query_text:
            st.info("ℹ️ Upload and load data first to run queries.")
        
        if run_query and query_text and run_query_enabled:
            with st.spinner("🔍 Interpreting your query…"):
                filters = nl_query_parser.parse_query_to_filters(query_text)
                is_valid, error_msg = nl_query_parser.validate_filters(filters)
                if not is_valid:
                    st.error(f"⚠️ {error_msg or 'Could not understand query. Please refine your question.'}")
                else:
                    # Save to history
                    if "query_history" not in st.session_state:
                        st.session_state.query_history = []
                    st.session_state.query_history.append({
                        "query_text": query_text,
                        "timestamp": datetime.now().isoformat(),
                        "source": "nl"
                    })
                    # Keep last 10 queries
                    st.session_state.query_history = st.session_state.query_history[-10:]
                    
                    st.session_state.last_query_text = query_text
                    st.session_state.last_filters = filters
                    st.session_state.last_query_source = "nl"
                    st.session_state.show_results = True
                    st.rerun()
        
        # Show last successful query
        if st.session_state.get("last_query_text"):
            st.markdown("---")
            st.caption(f"🕒 Last query: *\"{st.session_state.last_query_text}\"*")
    
    with main_col3:
        # SECTION D: Query History (Right Side, Modern Style)
        st.markdown("#### 📜 Recent Queries")
        
        if st.session_state.get("query_history"):
            history = st.session_state.query_history[-5:]  # Last 5
            history_reversed = list(reversed(history))
            
            # Clear history button
            if st.button("🗑️ Clear", key="clear_history", use_container_width=True):
                st.session_state.query_history = []
                st.rerun()
            
            st.markdown("---")
            
            for i, q_entry in enumerate(history_reversed):
                query_preview = q_entry["query_text"][:60] + "..." if len(q_entry["query_text"]) > 60 else q_entry["query_text"]
                timestamp = datetime.fromisoformat(q_entry["timestamp"]).strftime("%H:%M")
                
                # Modern card-style history item
                st.markdown(f"""
                <div style="padding: 0.75rem; margin-bottom: 0.5rem; background: #f8fafc; border-radius: 8px; border-left: 3px solid #3b82f6; cursor: pointer;" 
                     onclick="document.querySelector('[data-testid=\\'stTextInput\\']').value = '{q_entry['query_text'].replace("'", "\\'")}';">
                    <div style="font-size: 0.85rem; color: #1e293b; margin-bottom: 0.25rem;">{query_preview}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Clickable button to fill query
                if st.button("📝 Use", key=f"history_use_{i}", use_container_width=True):
                    st.session_state.query_text = q_entry["query_text"]
                    st.rerun()
        else:
            st.info("No query history yet. Run some queries to see them here.")


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
