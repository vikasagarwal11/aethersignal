"""
Drug Watchlist Tab - Daily Signal Monitor
The killer feature for safety teams: monitor multiple drugs simultaneously
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import signal_stats
import quantum_ranking


def show_watchlist_tab():
    """
    Display the Drug Watchlist tab for monitoring multiple drugs simultaneously.
    Users can paste a list of drugs and get ranked emerging signals.
    """
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### 🔬 Drug Watchlist – Daily Signal Monitor")
    st.caption(
        "Paste your portfolio drugs (one per line) and get ranked emerging signals in <90 seconds. "
        "This feature scans all cases for each drug and ranks potential safety signals."
    )

    default_drugs = "Wegovy\nOzempic\nMounjaro\nDupixent\nEylea\nLibtayo"
    watchlist = st.text_area(
        "Your drugs (one per line)",
        value=default_drugs,
        height=180,
        key="watchlist_input",
        help="Enter drug names, one per line. Case-insensitive matching will be used.",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_watch = st.button(
            "🚀 Run Daily Signal Watch",
            type="primary",
            use_container_width=True,
            key="run_watchlist",
        )

    if run_watch:
        if st.session_state.get("normalized_data") is None:
            st.error("❌ Please upload and load data first in Step 1.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        drugs = [d.strip() for d in watchlist.split("\n") if d.strip()]
        if not drugs:
            st.error("❌ Enter at least one drug name.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        normalized_df = st.session_state.normalized_data
        with st.spinner(
            f"🔍 Scanning {len(normalized_df):,} cases for {len(drugs)} drug(s)..."
        ):
            candidates = []
            for drug in drugs:
                temp_filter = {"drug": drug}
                filtered = signal_stats.apply_filters(normalized_df, temp_filter)
                if not filtered.empty:
                    combos = signal_stats.get_drug_event_combinations(
                        filtered, min_cases=5
                    )
                    for c in combos:
                        c["source_drug"] = drug
                    candidates.extend(combos)

            if candidates:
                # Apply quantum ranking
                ranked = quantum_ranking.quantum_rerank_signals(candidates)
                df = pd.DataFrame(ranked).head(50)

                st.success(
                    f"✅ Found {len(ranked)} potential signals → showing top 50 ranked by quantum score"
                )

                # Display results
                display_cols = [
                    "source_drug",
                    "reaction",
                    "count",
                    "quantum_score",
                    "quantum_rank",
                    "classical_rank",
                ]
                # Only show columns that exist
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(
                    df[available_cols],
                    use_container_width=True,
                    hide_index=True,
                )

                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📄 Download Full Report",
                    csv,
                    f"aethersignal_watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True,
                )

                # Track analytics
                if st.session_state.get("analytics_enabled"):
                    import analytics

                    analytics.log_event(
                        "watchlist_run",
                        {
                            "drug_count": len(drugs),
                            "signals_found": len(ranked),
                            "top_50_shown": len(df),
                        },
                    )
            else:
                st.info("ℹ️ No emerging signals found — all clear today! ✅")

    st.markdown("</div>", unsafe_allow_html=True)