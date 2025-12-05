"""
Social AE Dashboard UI component for AetherSignal.
Provides Streamlit interface for social media adverse event exploration.
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List
import plotly.express as px
import plotly.graph_objects as go

from .social_fetcher import fetch_daily_social_posts
from .social_cleaner import clean_and_normalize_posts
from .social_mapper import extract_reactions_from_posts, get_reaction_summary, normalize_to_meddra
from .social_anonymizer import anonymize_posts
from .social_severity import calculate_severity_for_posts
from .social_ae_storage import store_posts, get_posts, get_statistics, init_database
from .social_storage import store_social_records, load_recent_social, get_social_statistics
from .social_ae_scheduler import run_daily_pull, DEFAULT_DRUG_WATCHLIST
from src.literature_integration import enrich_signal_with_literature
from src.ai.timeseries_engine import TimeSeriesEngine


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
        options=["reddit", "x", "youtube"],
        default=["reddit"],
        key="social_ae_platforms",
        help="Select social media platforms to search (X and YouTube require API keys)",
    )
    
    if not platforms:
        st.warning("⚠️ Please select at least one platform.")
        return
    
    # Store drug terms in session state
    if drug_terms:
        st.session_state.social_ae_drug_terms = drug_terms
    
    # Tabs for different views (Phase 2: Added Intelligence tab)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Fetch & View", 
        "📈 Trends", 
        "🧠 Intelligence",  # NEW: Phase 2
        "📊 Database", 
        "⚙️ Automation"
    ])
    
    with tab1:
        render_fetch_tab(drug_terms, days_back, platforms)
    
    with tab2:
        render_trends_tab()
    
    with tab3:
        render_intelligence_tab()  # NEW: Phase 2
    
    with tab4:
        render_database_tab()
    
    with tab5:
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
                
                # Extract reactions with confidence scores (multi-AE mode enabled)
                df_with_reactions = extract_reactions_from_posts(cleaned_df, include_confidence=True, multi_ae=True)
                
                # Calculate severity scores
                df_with_reactions = calculate_severity_for_posts(df_with_reactions, reactions_col="reactions")
                
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
            if "reactions" in df.columns:
                # Multi-AE mode: count unique reactions across all posts
                all_reactions = []
                for reactions_list in df["reactions"]:
                    if isinstance(reactions_list, list):
                        all_reactions.extend(reactions_list)
                unique_reactions = len(set(all_reactions)) if all_reactions else 0
            else:
                unique_reactions = df["reaction"].nunique() if "reaction" in df.columns else 0
            st.metric("Reactions detected", unique_reactions)
        
        # Reaction summary (supports both single and multi-AE modes)
        has_reactions = False
        if "reactions" in df.columns:
            # Multi-AE mode
            has_reactions = df["reactions"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).any()
        elif "reaction" in df.columns:
            # Single-AE mode (backward compatibility)
            has_reactions = df["reaction"].notna().any()
        
        if has_reactions:
            st.markdown("---")
            st.markdown("#### 📊 Detected Reactions")
            
            reaction_summary = get_reaction_summary(df, multi_ae=("reactions" in df.columns))
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
                
                # Show multi-AE stats if available
                if "reaction_count" in df.columns:
                    st.caption(f"📈 Posts with multiple reactions: {(df['reaction_count'] > 1).sum()} ({(df['reaction_count'] > 1).sum() / len(df) * 100:.1f}%)")
                
                # Literature validation for top reactions
                if len(reaction_df) > 0:
                    st.markdown("---")
                    st.markdown("#### 📚 Validate Against Literature")
                    st.caption("Check if top reactions are mentioned in published literature or clinical trials")
                    
                    top_reactions = reaction_df.head(3)["Reaction"].tolist()
                    top_drugs = df["drug_match"].value_counts().head(3).index.tolist() if "drug_match" in df.columns else []
                    
                    if top_drugs and top_reactions:
                        selected_drug = st.selectbox(
                            "Select drug to validate",
                            options=top_drugs,
                            key="social_ae_lit_drug",
                        )
                        selected_reaction = st.selectbox(
                            "Select reaction to validate",
                            options=top_reactions,
                            key="social_ae_lit_reaction",
                        )
                        
                        if st.button("🔍 Search Literature", key="social_ae_search_lit"):
                            with st.spinner("Searching PubMed and ClinicalTrials.gov..."):
                                literature = enrich_signal_with_literature(selected_drug, selected_reaction)
                                
                                if literature['total_pubmed'] > 0 or literature['total_trials'] > 0:
                                    st.success(f"✅ Found {literature['total_pubmed']} PubMed articles and {literature['total_trials']} clinical trials")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**📄 PubMed Articles**")
                                        if literature['pubmed_articles']:
                                            for article in literature['pubmed_articles']:
                                                st.markdown(
                                                    f"**{article.get('title', 'N/A')}**  \n"
                                                    f"*{article.get('authors', 'N/A')}*  \n"
                                                    f"{article.get('journal', '')} ({article.get('year', 'N/A')})  \n"
                                                    f"[View]({article.get('url', '#')})"
                                                )
                                                st.markdown("---")
                                    
                                    with col2:
                                        st.markdown("**🧪 Clinical Trials**")
                                        if literature['clinical_trials']:
                                            for trial in literature['clinical_trials']:
                                                st.markdown(
                                                    f"**{trial.get('title', 'N/A')}**  \n"
                                                    f"Status: {trial.get('status', 'N/A')}  \n"
                                                    f"Phase: {', '.join(trial.get('phase', []))}  \n"
                                                    f"[View]({trial.get('url', '#')})"
                                                )
                                                st.markdown("---")
                                else:
                                    st.info("ℹ️ No literature evidence found. This may be a novel signal or require different search terms.")
        
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
        display_columns = ["text", "reactions", "reaction", "reaction_count", "confidence_score", "confidence_level", "platform", "drug_match", "created_date"]
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Format reactions column for display
        if "reactions" in filtered_df.columns:
            display_df = filtered_df.copy()
            display_df["reactions"] = display_df["reactions"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) and x else (x if pd.notna(x) else "None")
            )
        else:
            display_df = filtered_df.copy()
        
            if available_columns:
                # Limit display columns for readability
                display_df = display_df[available_columns].copy()
                
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
                        st.text_area("Post content", post.get("text", ""), height=200, disabled=True, label_visibility="collapsed")
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


def render_trends_tab():
    """Render the trends and time-series analysis tab."""
    st.markdown("#### 📈 Social AE Trends & Time-Series Analysis")
    st.caption("View trends over time for posts, reactions, and signals")
    
    # Load data from session state or database
    if "social_ae_data" in st.session_state and not st.session_state.social_ae_data.empty:
        df = st.session_state.social_ae_data
    else:
        # Try to load from database
        try:
            df = load_recent_social(days=30)
            if df.empty:
                df = get_posts(days_back=30, limit=5000)
        except Exception:
            df = get_posts(days_back=30, limit=5000)
    
    if df.empty:
        st.info("💡 No data available. Fetch posts in the 'Fetch & View' tab or load from database.")
        return
    
    # Check if we have date column
    date_col = None
    for col in ["created_date", "created_utc", "date", "timestamp"]:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        st.warning("⚠️ No date column found. Cannot generate trends.")
        return
    
    # Convert date column
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
    except Exception as e:
        st.error(f"Error parsing dates: {str(e)}")
        return
    
    if df.empty:
        st.warning("⚠️ No valid dates found after parsing.")
        return
    
    # Filter options
    st.markdown("---")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        if "drug_match" in df.columns:
            selected_drugs = st.multiselect(
                "Filter by Drug",
                options=sorted(df["drug_match"].unique().tolist()),
                default=[],
                key="trends_drug_filter"
            )
        else:
            selected_drugs = []
    
    with filter_col2:
        if "reaction" in df.columns:
            selected_reactions = st.multiselect(
                "Filter by Reaction",
                options=sorted(df["reaction"].dropna().unique().tolist()),
                default=[],
                key="trends_reaction_filter"
            )
        else:
            selected_reactions = []
    
    # Apply filters
    filtered_df = df.copy()
    if selected_drugs and "drug_match" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["drug_match"].isin(selected_drugs)]
    if selected_reactions and "reaction" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["reaction"].isin(selected_reactions)]
    
    # Time aggregation options
    st.markdown("---")
    agg_period = st.radio(
        "Time Period",
        options=["Daily", "Weekly", "Monthly"],
        horizontal=True,
        key="trends_agg_period"
    )
    
    # Aggregate by time period
    if agg_period == "Daily":
        filtered_df["period"] = filtered_df[date_col].dt.date
        period_label = "Day"
    elif agg_period == "Weekly":
        filtered_df["period"] = filtered_df[date_col].dt.to_period("W").astype(str)
        period_label = "Week"
    else:  # Monthly
        filtered_df["period"] = filtered_df[date_col].dt.to_period("M").astype(str)
        period_label = "Month"
    
    # Create trend data
    trend_data = filtered_df.groupby("period").size().reset_index(name="count")
    trend_data = trend_data.sort_values("period")
    
    if trend_data.empty:
        st.warning("No data available for selected filters.")
        return
    
    # Plot trendline
    st.markdown(f"### 📊 Posts Over Time ({agg_period})")
    
    fig = px.line(
        trend_data,
        x="period",
        y="count",
        markers=True,
        color_discrete_sequence=["#2563eb"],
        labels={"period": period_label, "count": "Number of Posts"}
    )
    fig.update_layout(
        xaxis_title=period_label,
        yaxis_title="Posts",
        height=400,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_tickangle=-45 if agg_period != "Daily" else 0
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Time-series analysis using TimeSeriesEngine
    if len(trend_data) >= 3:
        st.markdown("---")
        st.markdown("### 🔬 Time-Series Analysis")
        
        # Convert to Series for TimeSeriesEngine
        series = pd.Series(trend_data["count"].values, index=range(len(trend_data)))
        
        ts_engine = TimeSeriesEngine()
        
        # Moving average
        ma = ts_engine.compute_ma(series, window=3)
        trend_data["ma_3"] = ma.values
        
        # EWMA
        ewma = ts_engine.compute_ewma(series, alpha=0.3)
        trend_data["ewma"] = ewma.values
        
        # Plot with moving averages
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=trend_data["period"],
            y=trend_data["count"],
            mode='lines+markers',
            name='Observed',
            line=dict(color='#2563eb', width=2)
        ))
        fig2.add_trace(go.Scatter(
            x=trend_data["period"],
            y=trend_data["ma_3"],
            mode='lines',
            name='Moving Average (3)',
            line=dict(color='#10b981', width=2, dash='dash')
        ))
        fig2.add_trace(go.Scatter(
            x=trend_data["period"],
            y=trend_data["ewma"],
            mode='lines',
            name='EWMA (α=0.3)',
            line=dict(color='#f59e0b', width=2, dash='dot')
        ))
        fig2.update_layout(
            xaxis_title=period_label,
            yaxis_title="Posts",
            height=400,
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_tickangle=-45 if agg_period != "Daily" else 0,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Anomaly detection
        if len(trend_data) >= 4:
            try:
                anomalies = ts_engine.detect_anomalies(series, method="zscore", threshold=2.0)
                if anomalies:
                    st.markdown("**🚨 Detected Anomalies:**")
                    anomaly_periods = [trend_data.iloc[idx]["period"] for idx in anomalies]
                    anomaly_counts = [trend_data.iloc[idx]["count"] for idx in anomalies]
                    anomaly_df = pd.DataFrame({
                        period_label: anomaly_periods,
                        "Count": anomaly_counts
                    })
                    st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.caption(f"Anomaly detection unavailable: {str(e)}")
    
    # Reaction trends
    if "reaction" in filtered_df.columns and filtered_df["reaction"].notna().any():
        st.markdown("---")
        st.markdown("### 📊 Reaction Trends")
        
        reaction_trends = filtered_df.groupby(["period", "reaction"]).size().reset_index(name="count")
        top_reactions = filtered_df["reaction"].value_counts().head(5).index.tolist()
        reaction_trends_filtered = reaction_trends[reaction_trends["reaction"].isin(top_reactions)]
        
        if not reaction_trends_filtered.empty:
            fig3 = px.line(
                reaction_trends_filtered,
                x="period",
                y="count",
                color="reaction",
                markers=True,
                labels={"period": period_label, "count": "Count", "reaction": "Reaction"}
            )
            fig3.update_layout(
                xaxis_title=period_label,
                yaxis_title="Count",
                height=400,
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis_tickangle=-45 if agg_period != "Daily" else 0
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", len(filtered_df))
    with col2:
        latest_count = trend_data.iloc[-1]["count"] if not trend_data.empty else 0
        prev_count = trend_data.iloc[-2]["count"] if len(trend_data) >= 2 else 0
        delta = latest_count - prev_count if prev_count > 0 else 0
        st.metric("Latest Period", int(latest_count), delta=f"{delta:+}")
    with col3:
        avg_count = trend_data["count"].mean() if not trend_data.empty else 0
        st.metric("Average", f"{avg_count:.1f}")
    with col4:
        max_count = trend_data["count"].max() if not trend_data.empty else 0
        st.metric("Peak", int(max_count))


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
                options=["", "reddit", "x", "twitter", "youtube"],
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


def render_intelligence_tab():
    """
    Render the Intelligence tab (Phase 2: Social Intelligence Features).
    Includes: Spike detection, Novelty detection, Clustering, Cross-linking with FAERS.
    """
    st.markdown("#### 🧠 Social Intelligence Analysis")
    st.caption(
        "Advanced analysis: spike detection, novelty detection, clustering, and FAERS cross-linking. "
        "⚠️ Requires social data to be loaded."
    )
    
    # Try to load social data
    social_df = None
    if "social_ae_data" in st.session_state and not st.session_state.social_ae_data.empty:
        social_df = st.session_state.social_ae_data
    else:
        # Try to load from database
        try:
            from src.social_ae.social_storage import load_recent_social
            social_df = load_recent_social(days=30)
        except Exception:
            pass
    
    if social_df is None or social_df.empty:
        st.info("💡 No social data available. Fetch posts in the 'Fetch & View' tab first.")
        return
    
    # Initialize intelligence engine
    try:
        from src.social_ae.intelligence import SocialIntelligenceEngine
        intel_engine = SocialIntelligenceEngine()
    except Exception as e:
        st.error(f"Error initializing intelligence engine: {e}")
        return
    
    # Try to load FAERS data for cross-linking
    faers_df = None
    try:
        if "normalized_data" in st.session_state and st.session_state.normalized_data is not None:
            faers_df = st.session_state.normalized_data
        elif "data" in st.session_state and st.session_state.data is not None:
            faers_df = st.session_state.data
    except Exception:
        pass
    
    # Analysis controls
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        run_spike = st.button("🔍 Detect Spikes", use_container_width=True, type="primary")
        run_novelty = st.button("🆕 Detect Novel Reactions", use_container_width=True)
    
    with col2:
        run_clustering = st.button("🧩 Cluster Posts", use_container_width=True)
        run_crosslink = st.button("🔗 Cross-Link with FAERS", use_container_width=True, disabled=faers_df is None)
    
    if faers_df is None:
        st.info("💡 Load FAERS data in Quantum PV Explorer to enable cross-linking.")
    
    st.markdown("---")
    
    # Run analyses
    if run_spike:
        with st.spinner("Detecting spikes in social activity..."):
            spikes = intel_engine.detect_spikes(social_df)
            
            if spikes:
                st.subheader("📈 Detected Spikes")
                st.json(spikes)
                
                # Visualize spikes
                try:
                    import plotly.express as px
                    spike_df = pd.DataFrame(spikes)
                    spike_df["date"] = pd.to_datetime(spike_df["date"])
                    spike_df = spike_df.sort_values("date")
                    
                    fig = px.bar(
                        spike_df,
                        x="date",
                        y="count",
                        title="Social AE Activity Spikes",
                        labels={"count": "Post Count", "date": "Date"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not visualize spikes: {e}")
            else:
                st.info("No significant spikes detected.")
    
    if run_novelty:
        with st.spinner("Detecting novel reactions (present in social but not FAERS)..."):
            novel = intel_engine.detect_novel_reactions(social_df, faers_df)
            
            if novel:
                st.subheader("🆕 Novel Reactions (Social > FAERS)")
                
                novel_df = pd.DataFrame(novel)
                st.dataframe(novel_df, use_container_width=True)
                
                st.metric("Novel Reactions Found", len(novel))
                st.metric(
                    "Total Social Mentions", 
                    sum(novel_df["social_count"].tolist())
                )
            else:
                st.info("No novel reactions detected (or no FAERS data for comparison).")
    
    if run_clustering:
        with st.spinner("Clustering posts by content similarity..."):
            clusters = intel_engine.cluster_posts(social_df, n_clusters=5)
            
            if clusters:
                st.subheader("🧩 Post Clusters")
                
                for cluster in clusters:
                    with st.expander(
                        f"Cluster {cluster['cluster_id']} "
                        f"({cluster['size']} posts, {cluster['percentage']}%)"
                    ):
                        st.write("**Example posts:**")
                        for i, example in enumerate(cluster["examples"], 1):
                            st.write(f"{i}. {example[:200]}...")
            else:
                st.info("Clustering requires at least 5 posts with text content.")
    
    if run_crosslink and faers_df is not None:
        with st.spinner("Cross-linking social data with FAERS evidence..."):
            crosslink = intel_engine.crosslink_faers(social_df, faers_df)
            
            if crosslink:
                st.subheader("🔗 Cross-Linked Evidence (Social ↔ FAERS)")
                
                crosslink_df = pd.DataFrame(crosslink)
                st.dataframe(crosslink_df, use_container_width=True)
                
                st.metric("Matching Drug-Reaction Pairs", len(crosslink))
                
                # Summary by drug
                if "drug" in crosslink_df.columns:
                    drug_summary = crosslink_df.groupby("drug").size().sort_values(ascending=False)
                    st.write("**Matches by Drug:**")
                    st.dataframe(drug_summary.reset_index().rename(columns={0: "Match Count"}), use_container_width=True)
            else:
                st.info("No matching drug-reaction pairs found between social and FAERS data.")
    
    # Quick explainability section
    st.markdown("---")
    st.subheader("💡 Pattern Explanation")
    
    explain_col1, explain_col2 = st.columns(2)
    
    with explain_col1:
        explain_drug = st.text_input("Drug name", key="explain_drug", placeholder="e.g., semaglutide")
    
    with explain_col2:
        explain_reaction = st.text_input("Reaction", key="explain_reaction", placeholder="e.g., nausea")
    
    if st.button("Explain Pattern", use_container_width=True):
        if explain_drug and explain_reaction:
            # Check for spikes
            drug_reaction_df = social_df[
                (social_df.get("drug_match", pd.Series()).str.contains(explain_drug, case=False, na=False)) |
                (social_df.get("reaction", pd.Series()).str.contains(explain_reaction, case=False, na=False))
            ]
            
            spike_info = None
            if not drug_reaction_df.empty:
                spikes = intel_engine.detect_spikes(drug_reaction_df)
                if spikes:
                    spike_info = spikes[0]  # Use first spike
            
            # Check for novelty
            novel = intel_engine.detect_novel_reactions(
                social_df[social_df.get("reaction", pd.Series()).str.contains(explain_reaction, case=False, na=False)],
                faers_df
            )
            is_novel = any(r["reaction"].lower() == explain_reaction.lower() for r in novel)
            
            # Generate explanation
            explanation = intel_engine.explain_social_pattern(
                explain_drug,
                explain_reaction,
                spike_info,
                is_novel
            )
            
            st.info(explanation)
        else:
            st.warning("Please enter both drug and reaction names.")

