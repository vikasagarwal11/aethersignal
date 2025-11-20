"""
Social AE Dashboard UI component for AetherSignal.
Provides Streamlit interface for social media adverse event exploration.
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List

from .social_fetcher import fetch_daily_social_posts
from .social_cleaner import clean_and_normalize_posts
from .social_mapper import extract_reactions_from_posts, get_reaction_summary, normalize_to_meddra
from .social_anonymizer import anonymize_posts
from .social_ae_storage import store_posts, get_posts, get_statistics, init_database
from .social_storage import store_social_records, load_recent_social, get_social_statistics
from .social_ae_scheduler import run_daily_pull, DEFAULT_DRUG_WATCHLIST


def render_social_ae_module():
    """Render the Social AE Explorer module UI."""
    st.markdown("### 🌐 Social AE Explorer (BETA)")
    st.caption(
        "Pull daily potential adverse events from Reddit/X. "
        "⚠️ Exploratory only - not validated for regulatory use."
    )
    
    # Initialize database
    init_database()
    
    # Input section (shared across tabs)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        drug_terms = st.text_input(
            "Keywords / Drug names",
            value=st.session_state.get("social_ae_drug_terms", "ozempic, mounjaro, semaglutide"),
            key="social_ae_input",
            help="Enter comma-separated drug names or keywords to search",
            placeholder="e.g., ozempic, mounjaro, semaglutide",
        )
    
    with col2:
        days_back = st.number_input(
            "Days back",
            min_value=1,
            max_value=30,
            value=7,
            key="social_ae_days",
            help="How many days back to search",
        )
    
    # Platform selection
    platforms = st.multiselect(
        "Platforms",
        options=["reddit", "x"],
        default=["reddit"],
        key="social_ae_platforms",
        help="Select social media platforms to search (X requires API token)",
    )
    
    if not platforms:
        st.warning("⚠️ Please select at least one platform.")
        return
    
    # Store drug terms in session state
    if drug_terms:
        st.session_state.social_ae_drug_terms = drug_terms
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🔍 Fetch & View", "📊 Database", "⚙️ Automation"])
    
    with tab1:
        render_fetch_tab(drug_terms, days_back, platforms)
    
    with tab2:
        render_database_tab()
    
    with tab3:
        render_automation_tab()


def render_fetch_tab(drug_terms: str, days_back: int, platforms: List[str]):
    """Render the fetch and view tab."""
    st.markdown("---")
    
    # Options row
    opt_col1, opt_col2, opt_col3 = st.columns(3)
    
    with opt_col1:
        anonymize = st.checkbox(
            "🔒 Anonymize posts (remove PII)",
            value=True,
            key="social_ae_anonymize",
            help="Remove emails, phone numbers, usernames, and other PII for public use"
        )
    
    with opt_col2:
        store_in_db = st.checkbox(
            "💾 Store in database",
            value=True,
            key="social_ae_store_db",
            help="Save posts to Supabase/SQLite for historical tracking"
        )
    
    with opt_col3:
        use_ml = st.checkbox(
            "🤖 Use ML detection",
            value=False,
            key="social_ae_use_ml",
            help="Use DistilBERT for AE detection (slower but more accurate)"
        )
    
    # Fetch button
    run_fetch = st.button("🔍 Fetch latest posts", type="primary", use_container_width=True)
    
    if run_fetch and drug_terms:
        with st.spinner("Pulling social posts... This may take a moment."):
            try:
                # Fetch posts
                raw_posts = fetch_daily_social_posts(
                    drug_terms,
                    platforms=platforms,
                    limit_per_term=50,
                    days_back=days_back,
                )
                
                if not raw_posts:
                    st.warning("No posts found for the given keywords. Try different terms or increase days back.")
                    return
                
                # Clean and normalize (with optional ML)
                use_ml = st.session_state.get("social_ae_use_ml", False)
                cleaned_df = clean_and_normalize_posts(raw_posts, use_ml=use_ml)
                
                if cleaned_df.empty:
                    st.warning("All posts were filtered out as spam/low quality. Try different keywords.")
                    return
                
                # Extract reactions with confidence scores
                df_with_reactions = extract_reactions_from_posts(cleaned_df, include_confidence=True)
                
                # Anonymize if enabled
                if anonymize:
                    posts_list = df_with_reactions.to_dict('records')
                    anonymized_posts = anonymize_posts(posts_list)
                    df_final = pd.DataFrame(anonymized_posts)
                else:
                    df_final = df_with_reactions
                
                # Store in database if enabled
                if store_in_db:
                    # Try Supabase first (simplified storage), fallback to SQLite
                    try:
                        storage_result = store_social_records(df_final)
                        if storage_result.get("error"):
                            # Fallback to SQLite
                            posts_list = df_final.to_dict('records')
                            storage_result = store_posts(posts_list, drug_terms, platforms)
                            st.info(
                                f"💾 Stored {storage_result['stored']} new posts (SQLite), "
                                f"{storage_result['duplicates']} duplicates skipped"
                            )
                        else:
                            st.info(
                                f"💾 Stored {storage_result['inserted']} new posts (Supabase), "
                                f"{storage_result['errors']} errors"
                            )
                    except Exception as e:
                        # Fallback to SQLite
                        posts_list = df_final.to_dict('records')
                        storage_result = store_posts(posts_list, drug_terms, platforms)
                        st.info(
                            f"💾 Stored {storage_result['stored']} new posts (SQLite fallback), "
                            f"{storage_result['duplicates']} duplicates skipped"
                        )
                
                # Store in session state
                st.session_state.social_ae_data = df_final
                st.session_state.social_ae_fetched_at = datetime.now().isoformat()
                
                st.success(f"✅ Fetched {len(df_final)} cleaned posts")
                
            except Exception as e:
                st.error(f"❌ Error fetching posts: {str(e)}")
                return
    
    # Display results if available
    if "social_ae_data" in st.session_state and not st.session_state.social_ae_data.empty:
        df = st.session_state.social_ae_data
        
        st.markdown("---")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total posts", len(df))
        with col2:
            posts_with_reactions = df["has_reaction"].sum() if "has_reaction" in df.columns else 0
            st.metric("With reactions", posts_with_reactions)
        with col3:
            unique_drugs = df["drug_match"].nunique() if "drug_match" in df.columns else 0
            st.metric("Drugs mentioned", unique_drugs)
        with col4:
            unique_reactions = df["reaction"].nunique() if "reaction" in df.columns else 0
            st.metric("Reactions detected", unique_reactions)
        
        # Reaction summary
        if "reaction" in df.columns and df["reaction"].notna().any():
            st.markdown("---")
            st.markdown("#### 📊 Detected Reactions")
            
            reaction_summary = get_reaction_summary(df)
            if reaction_summary:
                reaction_df = pd.DataFrame(
                    list(reaction_summary.items()),
                    columns=["Reaction", "Count"]
                ).sort_values("Count", ascending=False)
                
                st.dataframe(reaction_df, use_container_width=True, hide_index=True)
                
                # Add MedDRA mapping if available
                reaction_df["MedDRA PT"] = reaction_df["Reaction"].apply(normalize_to_meddra)
                with st.expander("🔬 View with MedDRA mappings", expanded=False):
                    st.dataframe(reaction_df, use_container_width=True, hide_index=True)
        
        # Filter options
        st.markdown("---")
        st.markdown("#### 🔍 Filter Posts")
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            show_only_with_reactions = st.checkbox(
                "Show only posts with detected reactions",
                value=False,
                key="social_ae_filter_reactions",
            )
            
            # Confidence filter
            if "confidence_score" in df.columns:
                min_confidence = st.slider(
                    "Minimum confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    key="social_ae_min_confidence",
                    help="Filter posts by reaction detection confidence (0.0 = all, 1.0 = high confidence only)",
                )
            else:
                min_confidence = 0.0
        
        with filter_col2:
            if "platform" in df.columns:
                platform_filter = st.multiselect(
                    "Platform",
                    options=df["platform"].unique().tolist(),
                    default=df["platform"].unique().tolist(),
                    key="social_ae_filter_platform",
                )
            else:
                platform_filter = []
        
        with filter_col3:
            if "drug_match" in df.columns:
                drug_filter = st.multiselect(
                    "Drug",
                    options=df["drug_match"].unique().tolist(),
                    default=df["drug_match"].unique().tolist(),
                    key="social_ae_filter_drug",
                )
            else:
                drug_filter = []
        
        # Apply filters
        filtered_df = df.copy()
        
        if show_only_with_reactions and "has_reaction" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["has_reaction"] == True]
        
        if platform_filter and "platform" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["platform"].isin(platform_filter)]
        
        if drug_filter and "drug_match" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["drug_match"].isin(drug_filter)]
        
        # Confidence filter
        if "confidence_score" in filtered_df.columns and min_confidence > 0:
            filtered_df = filtered_df[filtered_df["confidence_score"] >= min_confidence]
        
        # Display filtered posts
        st.markdown("---")
        st.markdown(f"#### 📋 Posts ({len(filtered_df)} shown)")
        
        # Search within posts
        search_text = st.text_input(
            "🔎 Search in posts",
            key="social_ae_search",
            placeholder="Type to search post content...",
        )
        
        if search_text:
            filtered_df = filtered_df[
                filtered_df["text"].str.contains(search_text, case=False, na=False)
            ]
            st.caption(f"Showing {len(filtered_df)} posts matching '{search_text}'")
        
        # Display posts table
        display_columns = ["text", "reaction", "confidence_score", "confidence_level", "platform", "drug_match", "created_date"]
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if available_columns:
            # Limit display columns for readability
            display_df = filtered_df[available_columns].copy()
            
            # Truncate long text
            if "text" in display_df.columns:
                display_df["text"] = display_df["text"].apply(
                    lambda x: x[:200] + "..." if isinstance(x, str) and len(x) > 200 else x
                )
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400,
            )
        
        # Export options
        st.markdown("---")
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"social_ae_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        
        with export_col2:
            # Show full post details in expander
            with st.expander("📄 View full post details", expanded=False):
                if not filtered_df.empty:
                    selected_idx = st.selectbox(
                        "Select post",
                        range(len(filtered_df)),
                        format_func=lambda x: f"Post {x+1}: {filtered_df.iloc[x].get('text', '')[:50]}...",
                    )
                    
                    if selected_idx is not None:
                        post = filtered_df.iloc[selected_idx]
                        st.markdown("**Full text:**")
                        st.text_area("", post.get("text", ""), height=200, disabled=True)
                        st.markdown("**Metadata:**")
                        st.json({
                            "Platform": post.get("platform", "N/A"),
                            "Drug match": post.get("drug_match", "N/A"),
                            "Reaction": post.get("reaction", "N/A"),
                            "Date": str(post.get("created_date", "N/A")),
                            "URL": post.get("url", "N/A"),
                            "Score": post.get("score", "N/A"),
                        })
        
        # Info about data freshness
        if "social_ae_fetched_at" in st.session_state:
            fetched_at = datetime.fromisoformat(st.session_state.social_ae_fetched_at)
            st.caption(f"📅 Data fetched: {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        # Initial state - show instructions
        st.info(
            "💡 Enter drug keywords above and click 'Fetch latest posts' to start. "
            "The system will search Reddit and X (if configured) for recent mentions."
        )
        
        # Option to load from database
        if st.button("📂 Load from database", use_container_width=True):
            df_from_db = get_posts(days_back=days_back, limit=1000)
            if not df_from_db.empty:
                st.session_state.social_ae_data = df_from_db
                st.session_state.social_ae_fetched_at = datetime.now().isoformat()
                st.success(f"✅ Loaded {len(df_from_db)} posts from database")
                st.rerun()


def render_database_tab():
    """Render the database statistics and query tab."""
    st.markdown("#### 📊 Database Statistics")
    
    # Try Supabase first, fallback to SQLite
    try:
        stats = get_social_statistics()
        if not stats:
            # Fallback to SQLite
            stats = get_statistics()
    except Exception:
        stats = get_statistics()
    
    try:
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", f"{stats.get('total_posts', 0):,}")
        with col2:
            st.metric("With Reactions", f"{stats.get('with_reactions', 0):,}")
        with col3:
            st.metric("Unique Drugs", stats.get('unique_drugs', 0))
        with col4:
            st.metric("Unique Reactions", stats.get('unique_reactions', 0))
        
        # Posts by platform
        if stats.get('by_platform'):
            st.markdown("**Posts by Platform:**")
            platform_df = pd.DataFrame(
                list(stats['by_platform'].items()),
                columns=["Platform", "Count"]
            )
            st.dataframe(platform_df, use_container_width=True, hide_index=True)
        
        # Date range
        if stats.get('date_range'):
            st.markdown(f"**Date Range:** {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        
        # Recent pulls
        if stats.get('recent_pulls'):
            st.markdown("**Recent Pulls:**")
            pulls_df = pd.DataFrame(stats['recent_pulls'])
            st.dataframe(pulls_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("#### 🔍 Query Database")
        
        query_col1, query_col2 = st.columns(2)
        with query_col1:
            query_drug = st.text_input("Drug name (optional)", key="db_query_drug")
            query_reaction = st.text_input("Reaction (optional)", key="db_query_reaction")
        
        with query_col2:
            query_platform = st.selectbox(
                "Platform (optional)",
                options=["", "reddit", "x", "twitter"],
                key="db_query_platform"
            )
            query_days = st.number_input("Days back", min_value=1, max_value=365, value=30, key="db_query_days")
        
        if st.button("🔍 Query Database", use_container_width=True):
            # Try Supabase first, fallback to SQLite
            try:
                df_query = load_recent_social(days=query_days)
                if not df_query.empty:
                    # Apply filters
                    if query_drug:
                        df_query = df_query[df_query["drug_name"].str.contains(query_drug, case=False, na=False)]
                    if query_reaction:
                        df_query = df_query[df_query["reaction"] == query_reaction]
                    if query_platform:
                        df_query = df_query[df_query["source"] == query_platform]
            except Exception:
                # Fallback to SQLite
                df_query = get_posts(
                    drug_match=query_drug if query_drug else None,
                    reaction=query_reaction if query_reaction else None,
                    platform=query_platform if query_platform else None,
                    days_back=query_days
                )
            
            if not df_query.empty:
                st.session_state.social_ae_data = df_query
                st.success(f"✅ Found {len(df_query)} posts")
                st.rerun()
            else:
                st.warning("No posts found matching criteria")
    
    except Exception as e:
        st.error(f"Error loading database statistics: {str(e)}")


def render_automation_tab():
    """Render the automation/scheduler tab."""
    st.markdown("#### ⚙️ Daily Automation")
    st.caption("Run scheduled daily pulls with default drug watchlist")
    
    st.markdown("**Default Drug Watchlist:**")
    watchlist_str = ", ".join(DEFAULT_DRUG_WATCHLIST[:20])
    st.code(watchlist_str + ("..." if len(DEFAULT_DRUG_WATCHLIST) > 20 else ""))
    
    st.markdown("---")
    
    # Manual run button
    if st.button("▶️ Run Daily Pull Now", type="primary", use_container_width=True):
        with st.spinner("Running daily pull... This may take several minutes."):
            result = run_daily_pull(
                drug_terms=None,  # Use default watchlist
                platforms=["reddit"],
                days_back=1,
                limit_per_term=50,
                anonymize=True
            )
            
            if result["success"]:
                st.success(
                    f"✅ Pull complete! "
                    f"Fetched {result['posts_fetched']} posts, "
                    f"stored {result['posts_stored']} new posts"
                )
                st.json(result)
            else:
                st.error(f"❌ Pull failed: {result.get('error', 'Unknown error')}")
    
    st.markdown("---")
    st.markdown("#### 📅 Scheduled Jobs")
    st.info(
        "To set up automated daily pulls:\n\n"
        "1. **GitHub Actions**: Create `.github/workflows/daily_pull.yml`\n"
        "2. **Cron**: Add to crontab: `0 2 * * * python -m src.social_ae.social_ae_scheduler`\n"
        "3. **APScheduler**: Use the `run_scheduled_pull()` function\n\n"
        "See `src/social_ae/social_ae_scheduler.py` for details."
    )
    
    # Show recent pull history
    try:
        stats = get_statistics()
        if stats.get('recent_pulls'):
            st.markdown("**Recent Automated Pulls:**")
            pulls_df = pd.DataFrame(stats['recent_pulls'])
            st.dataframe(pulls_df, use_container_width=True, hide_index=True)
    except Exception:
        pass

