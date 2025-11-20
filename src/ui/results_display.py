"""
Results display component for AetherSignal.
Handles all result tabs: Overview, Signals, Trends, Cases, Report.
"""

import json
import time
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

from src import analytics
from src import advanced_stats
from src import nl_query_parser
from src import pdf_report
from src import quantum_ranking
from src import signal_stats
from src import subgroup_discovery
from src.app_helpers import (
    cached_get_summary_stats,
    format_reaction_with_meddra,
    render_filter_chips,
)
from src.utils import normalize_text, safe_divide


def _log_perf_event(label: str, duration: float, extra: Optional[Dict] = None) -> None:
    if not st.session_state.get("analytics_enabled"):
        return
    payload = {"label": label, "duration_ms": round(duration * 1000, 2)}
    if extra:
        payload.update(extra)
    analytics.log_event("perf_metric", payload)


def display_query_results(filters: Dict, query_text: str, normalized_df: pd.DataFrame):
    """
    Display query results using the analysis pipeline, with tabs.
    """
    source = st.session_state.get("last_query_source") or "nl"
    source_label = "Advanced search" if source == "advanced" else "Natural language query"

    # Validate key columns existence for filters
    missing_cols = []
    if "drug" in filters and "drug_name" not in normalized_df.columns:
        missing_cols.append("drug_name")
    if "reaction" in filters and "reaction" not in normalized_df.columns:
        missing_cols.append("reaction")
    if missing_cols:
        st.warning(
            "Some expected columns for these filters are missing in your dataset: "
            + ", ".join(missing_cols)
        )

    # Track query execution
    if st.session_state.get("analytics_enabled"):
        analytics.log_event(
            "query_executed",
            {
                "source": source,
                "has_drug": "drug" in filters,
                "has_reaction": "reaction" in filters,
                "quantum_enabled": st.session_state.get("quantum_enabled", False),
            },
        )
        
        # Audit logging for queries
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": "query_executed",
                "query": query_text[:100] if query_text else "",
                "filters": {k: str(v)[:50] for k, v in filters.items()},
                "source": source,
            }
            audit_file = analytics.ANALYTICS_DIR / "audit_log.jsonl"
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception:
            pass  # Silently fail
        
        # Add to query history
        query_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_text": query_text,
            "filters": filters,
            "source": source,
        }
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        st.session_state.query_history.append(query_entry)
        # Keep only last 20 queries
        if len(st.session_state.query_history) > 20:
            st.session_state.query_history = st.session_state.query_history[-20:]

    # Apply filters
    start_time = time.perf_counter()
    filtered_df = signal_stats.apply_filters(normalized_df, filters)
    _log_perf_event("apply_filters", time.perf_counter() - start_time, {"rows": len(normalized_df)})
    if filtered_df.empty:
        st.warning("No cases match the specified criteria.")
        if st.session_state.get("analytics_enabled"):
            analytics.log_event("query_no_results", {"source": source})
        return

    # Summary stats (cached)
    start_time = time.perf_counter()
    summary = cached_get_summary_stats(filtered_df, normalized_df)
    _log_perf_event("summary_stats", time.perf_counter() - start_time, {"matches": len(filtered_df)})

    overview_tab, signals_tab, trends_tab, cases_tab, report_tab = st.tabs(
        ["📊 Overview", "⚛️ Signals", "📅 Time & Co-reactions", "📋 Cases", "📄 Report"]
    )

    # ---------------- Overview Tab ----------------
    with overview_tab:
        _render_overview_tab(filters, source_label, summary, filtered_df, normalized_df)

    # ---------------- Signals Tab ----------------
    with signals_tab:
        _render_signals_tab(filters, summary, filtered_df, normalized_df)

    # ---------------- Trends & Co-reactions Tab ----------------
    with trends_tab:
        _render_trends_tab(filters, summary, filtered_df)

    # ---------------- Cases Tab ----------------
    with cases_tab:
        _render_cases_tab(filtered_df, normalized_df, summary)

    # ---------------- Report Tab ----------------
    with report_tab:
        _render_report_tab(filters, query_text, summary, source)


def _render_overview_tab(filters: Dict, source_label: str, summary: Dict, 
                         filtered_df: pd.DataFrame, normalized_df: pd.DataFrame):
    """Render Overview tab with KPIs and summary."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("Interpreted filters")
    st.caption(
        f"Source: **{source_label}** · "
        f"{nl_query_parser.filters_to_natural_language(filters)}"
    )
    # Show excluded reactions if present
    if filters.get('exclude_reaction'):
        excluded_terms = ', '.join(filters['exclude_reaction']) if isinstance(filters['exclude_reaction'], list) else filters['exclude_reaction']
        st.caption(f"❌ **Excluding:** {excluded_terms}")
    render_filter_chips(filters)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<p class='kpi-value'>{summary['matching_cases']:,}</p>"
            "<p class='kpi-label'>Matching cases</p>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<p class='kpi-value'>{summary['percentage']:.1f}%</p>"
            "<p class='kpi-label'>of dataset</p>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<p class='kpi-value'>{summary['serious_count']:,}</p>"
            "<p class='kpi-label'>Serious cases</p>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<p class='kpi-value'>{summary['serious_percentage']:.1f}%</p>"
            "<p class='kpi-label'>Serious among matches</p>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Top drugs / reactions
    if summary.get("top_drugs") or summary.get("top_reactions"):
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if summary.get("top_drugs"):
            with c1:
                st.markdown("#### Top drugs")
                td_df = pd.DataFrame(
                    list(summary["top_drugs"].items()), columns=["Drug", "Count"]
                )
                st.dataframe(td_df, use_container_width=True, hide_index=True)
        if summary.get("top_reactions"):
            with c2:
                st.markdown("#### Top reactions")
                # Enhance with MedDRA PTs if available
                reactions_data = []
                for reaction, count in summary["top_reactions"].items():
                    # Try to get MedDRA PT from normalized data
                    meddra_pt = None
                    if 'reaction_meddra' in normalized_df.columns and 'reaction' in normalized_df.columns:
                        matches = normalized_df[normalized_df['reaction'].astype(str).str.contains(str(reaction), case=False, na=False)]
                        if not matches.empty:
                            meddra_pt = matches['reaction_meddra'].iloc[0] if 'reaction_meddra' in matches.columns else None
                    
                    display_reaction = format_reaction_with_meddra(reaction, meddra_pt)
                    reactions_data.append({
                        "Reaction": display_reaction,
                        "Count": count
                    })
                
                tr_df = pd.DataFrame(reactions_data)
                st.dataframe(tr_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Geographic distribution (if country data available)
    if "country" in filtered_df.columns:
        country_counts = filtered_df["country"].value_counts().head(20)
        if len(country_counts) > 0:
            st.markdown("<div class='block-card'>", unsafe_allow_html=True)
            st.subheader("Geographic distribution")
            country_df = pd.DataFrame({
                "Country": country_counts.index,
                "Cases": country_counts.values,
            })
            st.dataframe(country_df, use_container_width=True, hide_index=True)
            
            # Bar chart for countries
            try:
                fig_country = px.bar(
                    country_df.head(15),
                    x="Cases",
                    y="Country",
                    orientation="h",
                    color="Cases",
                    color_continuous_scale="Blues",
                    title="Top 15 Countries by Case Count",
                )
                fig_country.update_layout(
                    height=400,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    yaxis={"categoryorder": "total ascending"},
                )
                st.plotly_chart(fig_country, use_container_width=True)
            except Exception:
                pass  # Silently fail if chart can't be created
            
            st.markdown("</div>", unsafe_allow_html=True)


def _render_signals_tab(filters: Dict, summary: Dict, filtered_df: pd.DataFrame, 
                       normalized_df: pd.DataFrame):
    """Render Signals tab with PRR/ROR and subgroup discovery."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("Disproportionality metrics (exploratory)")
    st.caption(
        "PRR and ROR are exploratory disproportionality metrics based on spontaneous reports. "
        "They are not validated for regulatory decision-making."
    )

    prr_ror_block_added = False
    if "drug" in filters and "reaction" in filters:
        drug = filters["drug"] if isinstance(filters["drug"], str) else filters["drug"][0]
        reaction = (
            filters["reaction"]
            if isinstance(filters["reaction"], str)
            else filters["reaction"][0]
        )
        prr_ror = signal_stats.calculate_prr_ror(drug, reaction, normalized_df)
        if prr_ror:
            # Guard against NaN/inf values
            prr_val = prr_ror.get('prr', 0)
            ror_val = prr_ror.get('ror', 0)
            
            if np.isnan(prr_val) or np.isinf(prr_val) or np.isnan(ror_val) or np.isinf(ror_val):
                st.warning("⚠️ Cannot calculate PRR/ROR: insufficient data or edge case detected.")
            elif summary['matching_cases'] < 3:
                st.info("ℹ️ Fewer than 3 matching cases. Interpret disproportionality metrics with caution.")
            else:
                prr_ror_block_added = True
                c1, c2, c3 = st.columns(3)
                with c1:
                    prr_ci_lower = prr_ror.get('prr_ci_lower', 0)
                    prr_ci_upper = prr_ror.get('prr_ci_upper', 0)
                    if np.isnan(prr_ci_lower) or np.isinf(prr_ci_lower):
                        prr_ci_lower = 0
                    if np.isnan(prr_ci_upper) or np.isinf(prr_ci_upper):
                        prr_ci_upper = 0
                    st.metric(
                        "PRR",
                        f"{prr_val:.2f}",
                        f"95% CI: {prr_ci_lower:.2f} – {prr_ci_upper:.2f}",
                    )
                with c2:
                    ror_ci_lower = prr_ror.get('ror_ci_lower', 0)
                    ror_ci_upper = prr_ror.get('ror_ci_upper', 0)
                    if np.isnan(ror_ci_lower) or np.isinf(ror_ci_lower):
                        ror_ci_lower = 0
                    if np.isnan(ror_ci_upper) or np.isinf(ror_ci_upper):
                        ror_ci_upper = 0
                    st.metric(
                        "ROR",
                        f"{ror_val:.2f}",
                        f"95% CI: {ror_ci_lower:.2f} – {ror_ci_upper:.2f}",
                    )
                with c3:
                    p_val = prr_ror.get("p_value")
                    if isinstance(p_val, (int, float)) and not (np.isnan(p_val) or np.isinf(p_val)):
                        st.metric("P-value", f"{p_val:.4f}")
                    else:
                        st.metric("P-value", "N/A")
                summary["prr_ror"] = prr_ror
                explanation = signal_stats.describe_signal(prr_ror)
                if explanation:
                    st.info(explanation)
                
                # Advanced statistics
                if prr_ror:
                    drug_mask = normalized_df["drug_name"].apply(
                        lambda x: normalize_text(str(drug)) in normalize_text(str(x))
                    )
                    reaction_mask = normalized_df["reaction"].apply(
                        lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
                    )
                    
                    a = ((drug_mask) & (reaction_mask)).sum()
                    b = (drug_mask & ~reaction_mask).sum()
                    c = (~drug_mask & reaction_mask).sum()
                    d = (~drug_mask & ~reaction_mask).sum()
                    
                    # IC and BCPNN
                    ic = advanced_stats.calculate_ic(a, b, c, d)
                    bcpnn = advanced_stats.calculate_bcpnn(a, b, c, d)
                    
                    # Statistical tests
                    chi2_result = advanced_stats.chi_square_test(a, b, c, d)
                    fisher_result = advanced_stats.fisher_exact_test(a, b, c, d)
                    
                    # Multiple confidence intervals
                    ci_90 = advanced_stats.calculate_prr_ror_ci(a, b, c, d, 0.90)
                    ci_95 = advanced_stats.calculate_prr_ror_ci(a, b, c, d, 0.95)
                    ci_99 = advanced_stats.calculate_prr_ror_ci(a, b, c, d, 0.99)
                    
                    # Signal strength
                    signal_strength, signal_color = advanced_stats.get_signal_strength(
                        prr_ror["prr"], ic["ic"], chi2_result["p_value"]
                    )
                    
                    st.markdown("---")
                    st.markdown("#### Advanced statistics")
                    
                    # IC/BCPNN
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("IC (Information Component)", f"{ic['ic']:.3f}", 
                                 f"95% CI: {ic['ic_025']:.3f} – {ic['ic_975']:.3f}")
                    with c2:
                        st.metric("BCPNN", f"{bcpnn['ic']:.3f}",
                                 f"95% CI: {bcpnn['ic_025']:.3f} – {bcpnn['ic_975']:.3f}")
                    
                    # Statistical tests
                    c3, c4 = st.columns(2)
                    with c3:
                        chi2_sig = "✓ Significant" if chi2_result["significant"] else "Not significant"
                        st.metric("Chi-square test", f"{chi2_result['chi2']:.4f}",
                                 f"P-value: {chi2_result['p_value']:.6f} ({chi2_sig})")
                    with c4:
                        fisher_sig = "✓ Significant" if fisher_result["significant"] else "Not significant"
                        st.metric("Fisher's exact test", f"{fisher_result['odds_ratio']:.4f}",
                                 f"P-value: {fisher_result['p_value']:.6f} ({fisher_sig})")
                    
                    # Multiple CIs
                    st.markdown("**Confidence intervals:**")
                    ci_df = pd.DataFrame({
                        "Metric": ["PRR", "PRR", "PRR", "ROR", "ROR", "ROR"],
                        "Level": ["90%", "95%", "99%", "90%", "95%", "99%"],
                        "Lower": [
                            ci_90["prr_ci_lower_90%"], ci_95["prr_ci_lower_95%"], ci_99["prr_ci_lower_99%"],
                            ci_90["ror_ci_lower_90%"], ci_95["ror_ci_lower_95%"], ci_99["ror_ci_lower_99%"],
                        ],
                        "Upper": [
                            ci_90["prr_ci_upper_90%"], ci_95["prr_ci_upper_95%"], ci_99["prr_ci_upper_99%"],
                            ci_90["ror_ci_upper_90%"], ci_95["ror_ci_upper_95%"], ci_99["ror_ci_upper_99%"],
                        ],
                    })
                    st.dataframe(ci_df, use_container_width=True, hide_index=True)
                    
                    # Signal strength
                    st.markdown(f"**Signal strength:** <span style='color:{signal_color}; font-weight:bold'>{signal_strength}</span>", 
                               unsafe_allow_html=True)
                    
                    # Subgroup Discovery
                    st.markdown("---")
                    st.markdown("#### 🔍 Subgroup Discovery")
                    st.caption(
                        "Automatically identifies demographic subgroups (age, sex, country) "
                        "where this drug-event signal is strongest."
                    )
                    
                    with st.spinner("Discovering significant subgroups..."):
                        subgroups = subgroup_discovery.discover_subgroups(
                            normalized_df, drug, reaction, min_cases=3
                        )
                    
                    has_subgroups = any(subgroups.values())
                    
                    if has_subgroups:
                        # Age subgroups
                        if subgroups.get('age'):
                            with st.expander(f"📊 Age subgroups ({len(subgroups['age'])} significant)", expanded=True):
                                age_data = []
                                for sg in subgroups['age']:
                                    age_data.append({
                                        'Age Group': sg['subgroup'],
                                        'Cases': sg['cases'],
                                        'PRR': f"{sg['prr']:.2f}",
                                        'ROR': f"{sg['ror']:.2f}",
                                    })
                                age_df = pd.DataFrame(age_data)
                                st.dataframe(age_df, use_container_width=True, hide_index=True)
                                st.caption(
                                    f"💡 Signal is strongest in: **{subgroups['age'][0]['subgroup']}** "
                                    f"(PRR: {subgroups['age'][0]['prr']:.2f})"
                                )
                        
                        # Sex subgroups
                        if subgroups.get('sex'):
                            with st.expander(f"👥 Sex subgroups ({len(subgroups['sex'])} significant)", expanded=True):
                                sex_data = []
                                for sg in subgroups['sex']:
                                    sex_data.append({
                                        'Sex': sg['subgroup'],
                                        'Cases': sg['cases'],
                                        'PRR': f"{sg['prr']:.2f}",
                                        'ROR': f"{sg['ror']:.2f}",
                                    })
                                sex_df = pd.DataFrame(sex_data)
                                st.dataframe(sex_df, use_container_width=True, hide_index=True)
                                if subgroups['sex']:
                                    st.caption(
                                        f"💡 Signal is strongest in: **{subgroups['sex'][0]['subgroup']}** "
                                        f"(PRR: {subgroups['sex'][0]['prr']:.2f})"
                                    )
                        
                        # Country subgroups
                        if subgroups.get('country'):
                            with st.expander(f"🌍 Country subgroups ({len(subgroups['country'])} significant)", expanded=True):
                                country_data = []
                                for sg in subgroups['country']:
                                    country_data.append({
                                        'Country': sg['subgroup'],
                                        'Cases': sg['cases'],
                                        'PRR': f"{sg['prr']:.2f}",
                                        'ROR': f"{sg['ror']:.2f}",
                                    })
                                country_df = pd.DataFrame(country_data)
                                st.dataframe(country_df, use_container_width=True, hide_index=True)
                                if subgroups['country']:
                                    st.caption(
                                        f"💡 Signal is strongest in: **{subgroups['country'][0]['subgroup']}** "
                                        f"(PRR: {subgroups['country'][0]['prr']:.2f})"
                                    )
                    else:
                        st.info(
                            "ℹ️ No significant demographic subgroups found. "
                            "This signal appears evenly distributed across age, sex, and country groups."
                        )

    if not prr_ror_block_added:
        st.info(
            "Select both a drug and a reaction (via NL or Advanced search) to calculate PRR/ROR."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Drug–event ranking
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("Drug–event signal ranking")
    st.caption(
        "Top drug–event pairs by case count (minimum 3 cases). "
        "Quantum-inspired mode favors rare, serious, and recent patterns."
    )

    combinations = signal_stats.get_drug_event_combinations(filtered_df, min_cases=3)
    if combinations:
        combos = combinations[:20]

        # Attach PRR/ROR for each combo
        for combo in combos:
            prr_ror = signal_stats.calculate_prr_ror(
                combo["drug"], combo["reaction"], normalized_df
            )
            if prr_ror:
                combo.update(prr_ror)

        # Add seriousness / date heuristics
        for combo in combos:
            cases = filtered_df.copy()
            if "drug_name" in cases.columns:
                mask_d = cases["drug_name"].apply(
                    lambda x: normalize_text(str(combo["drug"])) in normalize_text(str(x))
                )
                cases = cases[mask_d]
            if "reaction" in cases.columns and not cases.empty:
                mask_r = cases["reaction"].apply(
                    lambda x: normalize_text(str(combo["reaction"]))
                    in normalize_text(str(x))
                )
                cases = cases[mask_r]

            if not cases.empty:
                # Seriousness
                if "seriousness" in cases.columns:
                    serious_count = cases["seriousness"].apply(
                        lambda x: normalize_text(str(x))
                        in ["1", "yes", "y", "true", "serious"]
                    ).sum()
                    combo["serious_count"] = int(serious_count)
                    combo["seriousness"] = serious_count > 0
                else:
                    combo["serious_count"] = 0
                    combo["seriousness"] = False

                # Outcome
                if "outcome" in cases.columns:
                    outs = cases["outcome"].dropna().unique().tolist()
                    if outs:
                        combo["outcome"] = outs[0] if len(outs) == 1 else outs

                # Dates for recency
                if "onset_date" in cases.columns:
                    dates = cases["onset_date"].dropna().tolist()
                    if dates:
                        combo["dates"] = dates
                elif "report_date" in cases.columns:
                    dates = cases["report_date"].dropna().tolist()
                    if dates:
                        combo["dates"] = dates
            else:
                combo["serious_count"] = 0
                combo["seriousness"] = False

        # Classical ranking
        st.markdown("**Classical ranking (by case count):**")
        classical_df = pd.DataFrame(
            [
                {
                    "Rank": i + 1,
                    "Drug": c["drug"],
                    "Reaction": c["reaction"],
                    "Count": c["count"],
                    "PRR": f"{c.get('prr', 0):.2f}" if "prr" in c else "N/A",
                    "ROR": f"{c.get('ror', 0):.2f}" if "ror" in c else "N/A",
                }
                for i, c in enumerate(combos)
            ]
        )
        st.dataframe(classical_df, use_container_width=True, hide_index=True)
        
        # Enhanced visualization: PRR/ROR heatmap
        if len(combos) > 0:
            try:
                # Create heatmap for PRR values
                heatmap_data = []
                for combo in combos[:15]:  # Top 15 for readability
                    if "prr" in combo and isinstance(combo.get("prr"), (int, float)):
                        heatmap_data.append({
                            "Drug": combo["drug"][:30],  # Truncate long names
                            "Reaction": combo["reaction"][:30],
                            "PRR": combo["prr"],
                            "Count": combo["count"],
                        })
                
                if heatmap_data:
                    heatmap_df = pd.DataFrame(heatmap_data)
                    # Create pivot table for heatmap
                    pivot_df = heatmap_df.pivot_table(
                        values="PRR", 
                        index="Drug", 
                        columns="Reaction", 
                        fill_value=0
                    )
                    
                    # Only show heatmap if we have meaningful data
                    if pivot_df.shape[0] > 0 and pivot_df.shape[1] > 0:
                        fig_heatmap = px.imshow(
                            pivot_df.values,
                            labels=dict(x="Reaction", y="Drug", color="PRR"),
                            x=pivot_df.columns,
                            y=pivot_df.index,
                            aspect="auto",
                            color_continuous_scale="Reds",
                            title="PRR Heatmap (Top 15 Drug-Event Pairs)",
                        )
                        fig_heatmap.update_layout(height=400, plot_bgcolor="white", paper_bgcolor="white")
                        st.plotly_chart(fig_heatmap, use_container_width=True)
            except Exception:
                pass  # Silently fail if heatmap can't be created

        if st.session_state.get("quantum_enabled"):
            st.markdown("---")
            with st.spinner("Calculating quantum-inspired ranking…"):
                start_time = time.perf_counter()
                
                # Enhance with Social AE if enabled
                if st.session_state.get("include_social_ae", False):
                    try:
                        from src.social_ae.social_ae_integration import enhance_quantum_scores_with_social, load_social_ae_data
                        
                        social_ae_df = load_social_ae_data(days_back=30, use_supabase=True)
                        combos = enhance_quantum_scores_with_social(
                            combos,
                            social_ae_df,
                            social_weight=0.4
                        )
                    except Exception:
                        pass  # Continue without social enhancement if it fails
                
                ranked = quantum_ranking.quantum_rerank_signals(
                    combos, total_cases=len(normalized_df)
                )
                _log_perf_event("quantum_rank", time.perf_counter() - start_time, {"pairs": len(combos)})

            st.markdown(
                "**Quantum-inspired ranking (deterministic heuristic; no real hardware in demo):**"
            )
            st.caption(
                "ℹ️ Current demo runs fully on simulator – no real quantum hardware is used. "
                "This is a deterministic heuristic inspired by quantum search algorithms."
            )
            # Enhance reactions with MedDRA PTs
            q_data = []
            for i, c in enumerate(ranked[:10]):
                reaction = c.get("reaction", "")
                # Get MedDRA PT from normalized data
                meddra_pt = None
                if 'reaction_meddra' in normalized_df.columns:
                    matches = normalized_df[normalized_df['reaction'].astype(str).str.contains(str(reaction), case=False, na=False)]
                    if not matches.empty:
                        meddra_pt = matches['reaction_meddra'].iloc[0] if 'reaction_meddra' in matches.columns else None
                
                display_reaction = format_reaction_with_meddra(reaction, meddra_pt)
                
                row_data = {
                    "Rank": c.get("quantum_rank", i + 1),
                    "Drug": c["drug"],
                    "Reaction": display_reaction,
                    "Count": c["count"],
                    "Quantum score": round(c.get("quantum_score", 0.0), 3),
                    "PRR": f"{c.get('prr', 0):.2f}" if "prr" in c else "N/A",
                    "ROR": f"{c.get('ror', 0):.2f}" if "ror" in c else "N/A",
                }
                
                # Add social count if available
                if "social_count" in c:
                    row_data["Social signals"] = c["social_count"]
                
                q_data.append(row_data)
            q_df = pd.DataFrame(q_data)
            st.dataframe(q_df, use_container_width=True, hide_index=True)

            comp = quantum_ranking.compare_classical_vs_quantum(ranked, top_n=10)
            comp_df = pd.DataFrame(comp)
            st.markdown("**Shift vs classical ranking:**")
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.caption(
                "Positive shift = surfaced earlier in quantum-inspired ranking compared to classical frequency."
            )
    else:
        st.info("No drug–event pairs with at least 3 cases.")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_trends_tab(filters: Dict, summary: Dict, filtered_df: pd.DataFrame):
    """Render Trends tab with time trends and co-reactions."""
    # Time trend
    if summary.get("time_trend"):
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("Cases over time")
        trend_data = summary["time_trend"]
        trend_df = pd.DataFrame(list(trend_data.items()), columns=["Period", "Count"])
        trend_df["Period"] = pd.to_datetime(trend_df["Period"])
        trend_df = trend_df.sort_values("Period")

        fig = px.line(
            trend_df,
            x="Period",
            y="Count",
            markers=True,
            color_discrete_sequence=["#2563eb"],
        )
        fig.update_layout(
            xaxis_title="Period",
            yaxis_title="Cases",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)
        if len(trend_df) >= 2:
            latest = trend_df.iloc[-1]
            previous = trend_df.iloc[-2]
            delta = latest["Count"] - previous["Count"]
            pct = safe_divide(delta, previous["Count"], 0) * 100
            prev_label = previous["Period"].strftime("%b %Y")
            st.metric(
                "Latest vs prior period",
                f"{int(latest['Count'])}",
                f"{delta:+} ({pct:.1f}%) vs {prev_label}",
            )
        if len(trend_df) >= 12:
            latest_window = trend_df.iloc[-12:]["Count"].sum()
            prior_window = trend_df.iloc[-24:-12]["Count"].sum() if len(trend_df) >= 24 else None
            if prior_window:
                pct = safe_divide(latest_window - prior_window, prior_window, 0) * 100
                st.caption(
                    f"Last 12 periods: {latest_window:,} cases vs {prior_window:,} in the previous 12 "
                    f"({pct:+.1f}%)."
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # Co-reactions
    reaction_filter = filters.get("reaction")
    reaction = (
        reaction_filter
        if isinstance(reaction_filter, str)
        else (reaction_filter or [None])[0]
    )
    top_co_reactions = signal_stats.get_top_co_reactions(
        filtered_df, reaction=reaction, top_n=10
    )
    if top_co_reactions:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("Top co-occurring reactions")
        # Enhance with MedDRA PTs
        co_data = []
        for item in top_co_reactions:
            reaction_term = item.get('reaction', '')
            count = item.get('count', 0)
            # Get MedDRA PT from filtered data
            meddra_pt = None
            if 'reaction_meddra' in filtered_df.columns:
                matches = filtered_df[filtered_df['reaction'].astype(str).str.contains(str(reaction_term), case=False, na=False)]
                if not matches.empty:
                    meddra_pt = matches['reaction_meddra'].iloc[0] if 'reaction_meddra' in matches.columns else None
            
            display_reaction = format_reaction_with_meddra(reaction_term, meddra_pt)
            co_data.append({
                'Reaction': display_reaction,
                'Count': count
            })
        co_df = pd.DataFrame(co_data)
        st.dataframe(co_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    elif not summary.get("time_trend"):
        st.info("Time trend and co-reaction data not available for this query.")


def _render_cases_tab(filtered_df: pd.DataFrame, normalized_df: pd.DataFrame, summary: Dict):
    """Render Cases tab with data table and export."""
    if len(filtered_df) < 10:
        st.info(
            f"ℹ️ **Small sample size** ({len(filtered_df)} cases). "
            "Interpret disproportionality metrics with caution. "
            "Statistical tests may have limited power with fewer than 10 cases."
        )
    
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("Matching cases")
    max_rows = 1000
    show_df = filtered_df.head(max_rows)
    
    # Export buttons
    export_col1, export_col2 = st.columns(2)
    csv_data = None
    with export_col1:
        csv_data = show_df.to_csv(index=False).encode("utf-8")
        if st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"aethersignal_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        ):
            if st.session_state.get("analytics_enabled"):
                analytics.log_event("csv_export", {"row_count": len(show_df)})
    with export_col2:
        # Excel export requires openpyxl (already in requirements)
        try:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                show_df.to_excel(writer, index=False, sheet_name="Cases")
                # Also add summary sheet
                summary_sheet = pd.DataFrame({
                    "Metric": ["Total Cases", "Matching Cases", "Percentage"],
                    "Value": [
                        len(normalized_df),
                        len(filtered_df),
                        f"{summary['percentage']:.2f}%",
                    ],
                })
                summary_sheet.to_excel(writer, index=False, sheet_name="Summary")
            excel_data = excel_buffer.getvalue()
            if st.download_button(
                label="📊 Download as Excel",
                data=excel_data,
                file_name=f"aethersignal_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            ):
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event("excel_export", {"row_count": len(show_df)})
        except Exception:
            st.info("Excel export requires openpyxl. Install: pip install openpyxl")
    
    st.dataframe(show_df, use_container_width=True, height=420)
    if len(filtered_df) > max_rows:
        st.info(
            f"Showing first {max_rows:,} of {len(filtered_df):,} matching cases. "
            "Use export buttons above to download full filtered dataset."
        )
    else:
        st.info(f"Showing all {len(filtered_df):,} matching cases.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def _render_report_tab(filters: Dict, query_text: str, summary: Dict, source: str):
    """Render Report tab with PDF generation."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("One-page PDF summary")
    st.caption(
        "Generate a compact PDF snapshot of this query for email or slides. "
        "Reminder: exploratory only, not validated for regulatory use."
    )

    query_source_label = (
        "Advanced search form"
        if st.session_state.get("last_query_source") == "advanced"
        else "Natural language"
    )
    pdf_summary = pdf_report.create_summary_dict(
        query=query_text,
        filters=filters,
        total_cases=summary["total_cases"],
        matching_cases=summary["matching_cases"],
        percentage=summary["percentage"],
        prr_ror=summary.get("prr_ror"),
        top_drugs=summary.get("top_drugs"),
        top_reactions=summary.get("top_reactions"),
        age_stats=summary.get("age_stats"),
        sex_distribution=summary.get("sex_distribution"),
        serious_count=summary["serious_count"],
        serious_percentage=summary["serious_percentage"],
        time_trend=summary.get("time_trend"),
        query_source=query_source_label,
    )
    pdf_bytes = pdf_report.build_pdf_report(pdf_summary)
    if st.download_button(
        label="📥 Download PDF report",
        data=pdf_bytes,
        file_name=f"aethersignal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    ):
        if st.session_state.get("analytics_enabled"):
            analytics.log_event("pdf_download", {
                "query_source": source,
                "has_prr_ror": "prr_ror" in summary and summary["prr_ror"] is not None,
            })
            
            # Audit logging for PDF
            try:
                audit_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "pdf_generated",
                    "query": query_text[:100] if query_text else "",
                    "filters": {k: str(v)[:50] for k, v in filters.items()},
                    "source": source,
                    "matching_cases": summary["matching_cases"],
                }
                audit_file = analytics.ANALYTICS_DIR / "audit_log.jsonl"
                with open(audit_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(audit_entry) + "\n")
            except Exception:
                pass  # Silently fail
    
    st.markdown("</div>", unsafe_allow_html=True)

