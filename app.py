"""
AetherSignal – Quantum PV Explorer
Streamlit front-end: advanced UI + tabs + NL query + advanced filters.
"""

import json
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Set

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

import faers_loader
import nl_query_parser
import pdf_report
import pv_schema
import quantum_ranking
import signal_stats
from utils import normalize_text
import analytics
import advanced_stats
import watchlist_tab
import subgroup_discovery
from styles import apply_theme


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
# Session state
# -------------------------------------------------------------------
DEFAULT_SESSION_KEYS = {
    "data": None,
    "schema_mapping": {},
    "normalized_data": None,
    "last_filters": None,
    "last_query_text": "",
    "last_query_source": None,
    "quantum_enabled": False,
    "show_results": False,
    "query_history": [],
    "analytics_enabled": True,
}

for key, default in DEFAULT_SESSION_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# -------------------------------------------------------------------
# Helpers with caching
# -------------------------------------------------------------------
def load_all_files(uploaded_files) -> Optional[pd.DataFrame]:
    """
    Best-effort loader: tries FAERS helpers, PDF extraction, and CSV/Excel.
    """
    if not uploaded_files:
        return None

    frames: List[pd.DataFrame] = []
    processed_files: Set[int] = set()

    def _reset_file_pointer(file_obj):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    # 1) Try FAERS ZIP / ASCII detection via faers_loader
    faers_like_files = [f for f in uploaded_files if f.name.lower().endswith((".zip", ".txt"))]
    if faers_like_files:
        for f in faers_like_files:
            try:
                if f.name.lower().endswith(".zip"):
                    df = faers_loader.load_faers_zip(f)
                else:
                    df = faers_loader.load_faers_file(f)
                if df is not None and not df.empty:
                    frames.append(df)
                    processed_files.add(id(f))
                    continue
            except Exception:
                pass  # will fall back to generic parsing

    # 2) PDFs via faers_loader.load_pdf_files
    pdf_files = [f for f in uploaded_files if f.name.lower().endswith(".pdf")]
    if pdf_files:
        try:
            pdf_df = faers_loader.load_pdf_files(pdf_files)
            if pdf_df is not None and not pdf_df.empty:
                frames.append(pdf_df)
        except Exception:
            pass

    # 3) CSV / Excel / txt / generic zip
    for file in uploaded_files:
        if id(file) in processed_files:
            continue
        name = file.name.lower()
        if name.endswith(".pdf"):
            continue  # already handled
        try:
            _reset_file_pointer(file)
            if name.endswith(".csv"):
                frames.append(pd.read_csv(file))
            elif name.endswith((".xlsx", ".xls")):
                frames.append(pd.read_excel(file))
            elif name.endswith(".txt"):
                try:
                    frames.append(pd.read_csv(file, sep=","))
                except Exception:
                    # Fallback: whitespace-delimited TXT (e.g., FAERS-like exports)
                    frames.append(pd.read_csv(file, sep=r"\s+"))
            elif name.endswith(".zip"):
                # If not caught by FAERS logic, attempt CSV in zip
                with zipfile.ZipFile(file, "r") as z:
                    for fn in z.namelist():
                        if fn.lower().endswith(".csv"):
                            with z.open(fn) as f:
                                frames.append(pd.read_csv(f))
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner=False)
def _cached_detect_and_normalize(raw_df: pd.DataFrame):
    """
    Cached schema detection and normalization.
    """
    mapping = pv_schema.detect_schema(raw_df)
    normalized = pv_schema.normalize_dataframe(raw_df, mapping)
    return mapping, normalized


def _format_reaction_with_meddra(reaction: str, meddra_pt: Optional[str] = None) -> str:
    """
    Format reaction term with MedDRA PT for display.
    
    Args:
        reaction: Original reaction term
        meddra_pt: MedDRA Preferred Term (optional)
        
    Returns:
        Formatted string: "Reaction (MedDRA PT: Pyrexia)" or just "Reaction" if no mapping
    """
    if pd.isna(reaction) or not reaction:
        return ""
    
    reaction_str = str(reaction).strip()
    
    # If MedDRA PT exists and is different from original, show both
    if meddra_pt and meddra_pt.strip() and normalize_text(meddra_pt) != normalize_text(reaction_str):
        return f"{reaction_str} (MedDRA PT: {meddra_pt})"
    
    return reaction_str


@st.cache_data(show_spinner=False)
def _cached_get_summary_stats(filtered_df: pd.DataFrame, normalized_df: pd.DataFrame):
    """
    Cached summary statistics calculation.
    """
    return signal_stats.get_summary_stats(filtered_df, normalized_df)


def render_filter_chips(filters: Dict):
    """Render small filter chips under the interpreted filter text."""
    chips = []

    if "drug" in filters:
        drug = filters["drug"] if isinstance(filters["drug"], str) else ", ".join(filters["drug"])
        chips.append(f"<span class='filter-chip'>💊 {drug}</span>")

    if "reaction" in filters:
        reaction = (
            filters["reaction"]
            if isinstance(filters["reaction"], str)
            else ", ".join(filters["reaction"])
        )
        chips.append(f"<span class='filter-chip'>⚡ {reaction}</span>")

    if "age_min" in filters or "age_max" in filters:
        if "age_min" in filters and "age_max" in filters:
            label = f"{filters['age_min']}–{filters['age_max']}"
        elif "age_min" in filters:
            label = f"≥{filters['age_min']}"
        else:
            label = f"≤{filters['age_max']}"
        chips.append(f"<span class='filter-chip'>👤 Age {label}</span>")

    if "sex" in filters:
        chips.append(f"<span class='filter-chip'>👥 Sex: {filters['sex']}</span>")

    if "country" in filters:
        chips.append(f"<span class='filter-chip'>🌍 {filters['country']}</span>")

    if filters.get("seriousness"):
        chips.append("<span class='filter-chip'>⚠️ Serious cases only</span>")

    if "date_from" in filters or "date_to" in filters:
        txt = []
        if "date_from" in filters:
            txt.append(f"from {filters['date_from']}")
        if "date_to" in filters:
            txt.append(f"to {filters['date_to']}")
        chips.append(f"<span class='filter-chip'>📅 {' '.join(txt)}</span>")

    if "exclude_reaction" in filters:
        excluded = (
            filters["exclude_reaction"]
            if isinstance(filters["exclude_reaction"], str)
            else ", ".join(filters["exclude_reaction"])
        )
        chips.append(f"<span class='filter-chip'>❌ Excluding: {excluded}</span>")

    if chips:
        st.markdown("".join(chips), unsafe_allow_html=True)


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
    filtered_df = signal_stats.apply_filters(normalized_df, filters)
    if filtered_df.empty:
        st.warning("No cases match the specified criteria.")
        if st.session_state.get("analytics_enabled"):
            analytics.log_event("query_no_results", {"source": source})
        return

    # Summary stats (cached)
    summary = _cached_get_summary_stats(filtered_df, normalized_df)

    overview_tab, signals_tab, trends_tab, cases_tab, report_tab = st.tabs(
        ["📊 Overview", "⚛️ Signals", "📅 Time & Co-reactions", "📋 Cases", "📄 Report"]
    )

    # ---------------- Overview Tab ----------------
    with overview_tab:
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
                        
                        display_reaction = _format_reaction_with_meddra(reaction, meddra_pt)
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

    # ---------------- Signals Tab ----------------
    with signals_tab:
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
                    ranked = quantum_ranking.quantum_rerank_signals(
                        combos, total_cases=len(normalized_df)
                    )

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
                    
                    display_reaction = _format_reaction_with_meddra(reaction, meddra_pt)
                    q_data.append({
                        "Rank": c.get("quantum_rank", i + 1),
                        "Drug": c["drug"],
                        "Reaction": display_reaction,
                        "Count": c["count"],
                        "Quantum score": round(c.get("quantum_score", 0.0), 3),
                        "PRR": f"{c.get('prr', 0):.2f}" if "prr" in c else "N/A",
                        "ROR": f"{c.get('ror', 0):.2f}" if "ror" in c else "N/A",
                    })
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

    # ---------------- Trends & Co-reactions Tab ----------------
    with trends_tab:
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
                
                display_reaction = _format_reaction_with_meddra(reaction_term, meddra_pt)
                co_data.append({
                    'Reaction': display_reaction,
                    'Count': count
                })
            co_df = pd.DataFrame(co_data)
            st.dataframe(co_df, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        elif not summary.get("time_trend"):
            st.info("Time trend and co-reaction data not available for this query.")

    # ---------------- Cases Tab ----------------
    with cases_tab:
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
                from io import BytesIO
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

    # ---------------- Report Tab ----------------
    with report_tab:
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


# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
# Full-width hero
st.markdown(
    """
    <div class="main-hero">
        <div class="hero-badge">
            <span class="hero-badge-dot"></span>
            Live demo · Session-based only
        </div>
        <h1>AetherSignal – Quantum PV Explorer</h1>
        <p>Upload safety datasets, ask PV questions in natural language,
           and explore exploratory signals with quantum-inspired ranking.</p>
        <div class="hero-pill-row">
            <div class="hero-pill pill-session">
                <span>🟢</span> Session-based only · No data stored
            </div>
            <div class="hero-pill pill-faers">
                <span>📂</span> FAERS / CSV / Excel / PDF exports
            </div>
            <div class="hero-pill pill-quantum">
                <span>⚛️</span> Quantum-inspired ranking (demo)
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Reset button removed from main area - now in sidebar

st.markdown(
    """
    <div class="inline-banner">
        <strong>⚠️ Exploratory use only.</strong>
        Data is processed in-memory within this browser session and is cleared when you reset or close the tab.
        Spontaneous reports are subject to under-reporting and bias; no incidence or causality implied.
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# STEP 1 – UPLOAD & SCHEMA
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="session-chip-row" style="margin-bottom: 16px !important;">
        <div class="session-chip">🗂 Session-based, no login</div>
        <div class="session-chip">📄 Works with FAERS / CSV / Excel / PDF exports</div>
        <div class="session-chip">⚛️ Quantum-inspired ranking (demo)</div>
    </div>
    <div class='block-card' style="margin-top: 0 !important;">
        <h3>📤 1️⃣ Upload safety dataset</h3>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Drop FAERS ASCII, Argus/Veeva exports, CSV, Excel, text, ZIP or PDF",
    type=["csv", "xlsx", "xls", "txt", "zip", "pdf"],
    accept_multiple_files=True,
    help=(
        "You can upload multiple files. FAERS ASCII (DEMO/DRUG/REAC/OUTC…), "
        "Argus/Veeva exports, or ad-hoc CSV/Excel are supported."
    ),
)

load_clicked = st.button("🔄 Load & map data", disabled=not uploaded_files)

if load_clicked and uploaded_files:
    with st.spinner("Loading and mapping data…"):
        raw_df = load_all_files(uploaded_files)
        if raw_df is None or raw_df.empty:
            st.error("❌ Could not read any rows from the provided files. Please verify formats.")
            
            # Add helpful suggestions
            st.markdown("**💡 What to try:**")
            st.markdown("""
            - **FAERS exports**: Ensure you upload all 7 ASCII files (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR) 
              or a ZIP containing them.
            - **Argus/Veeva exports**: Export as CSV or Excel. Column names should include drug/reaction identifiers.
            - **CSV files**: Ensure proper comma separation and headers in the first row.
            - **Excel files**: Check that data starts in row 1 with headers.
            - **PDF files**: Only tabular PDFs are supported. Try exporting to CSV/Excel instead.
            """)
            
            if st.session_state.get("analytics_enabled"):
                analytics.log_event("upload_failed", {"file_count": len(uploaded_files)})
        else:
            st.session_state.data = raw_df
            if st.session_state.get("analytics_enabled"):
                analytics.log_event(
                    "upload_success",
                    {
                        "file_count": len(uploaded_files),
                        "row_count": len(raw_df),
                        "columns": len(raw_df.columns),
                    },
                )

            # Use cached detection and normalization
            mapping, normalized = _cached_detect_and_normalize(raw_df)
            st.session_state.schema_mapping = mapping

            essential = ["drug_name", "reaction", "case_id"]
            found = [f for f in essential if f in mapping]
            if len(found) == 0:
                st.error(
                    "Critical: could not detect any essential PV fields "
                    "(drug_name, reaction, case_id). Check column names or input format."
                )
            elif len(found) < 2:
                st.warning(
                    "Only detected "
                    f"{len(found)} essential field(s): {', '.join(found)}. "
                    "Some analysis features may be limited."
                )
            st.session_state.normalized_data = normalized
            st.success(f"✅ Loaded {len(raw_df):,} rows")

            # Dataset snapshot KPIs
            try:
                drugs = (
                    normalized["drug_name"].nunique() if "drug_name" in normalized.columns else 0
                )
                reactions = (
                    normalized["reaction"].nunique() if "reaction" in normalized.columns else 0
                )

                dates = None
                if "onset_date" in normalized.columns:
                    dates = pd.to_datetime(normalized["onset_date"], errors="coerce")
                elif "report_date" in normalized.columns:
                    dates = pd.to_datetime(normalized["report_date"], errors="coerce")

                if dates is not None:
                    dates = dates.dropna()
                    min_date = dates.min()
                    max_date = dates.max()
                else:
                    min_date = max_date = None

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f"<p class='kpi-value'>{len(raw_df):,}</p>"
                        "<p class='kpi-label'>Rows loaded</p>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"<p class='kpi-value'>{drugs:,}</p>"
                        "<p class='kpi-label'>Distinct drugs</p>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<p class='kpi-value'>{reactions:,}</p>"
                        "<p class='kpi-label'>Distinct reactions</p>",
                        unsafe_allow_html=True,
                    )

                if min_date and max_date:
                    st.caption(
                        f"Detected date range: **{min_date.date().isoformat()} – {max_date.date().isoformat()}**"
                    )
            except Exception:
                pass

            if mapping:
                with st.expander("Detected schema mapping", expanded=False):
                    st.dataframe(
                        pv_schema.get_schema_summary(mapping),
                        use_container_width=True,
                        hide_index=True,
                    )
            st.session_state.show_results = False
            st.rerun()

elif not uploaded_files:
    st.info("Upload at least one file to get started.")
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# MAIN QUERY FLOW (only when data is loaded)
# -------------------------------------------------------------------
if st.session_state.data is not None and st.session_state.normalized_data is not None:
    normalized_df = st.session_state.normalized_data

    # Create tabs for different query modes
    query_tab, watchlist_tab_ui, advanced_tab = st.tabs([
        "💬 Natural Language Query",
        "🔬 Drug Watchlist",
        "⚙️ Advanced Search"
    ])

    with query_tab:
        # 2 – Query (Suggested NL + freeform)
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

    with watchlist_tab_ui:
        watchlist_tab.show_watchlist_tab()

    with advanced_tab:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Advanced Search")
        st.info("💡 Use the sidebar filters for structured search, or use the Natural Language Query tab for free-form questions.")
        st.markdown("</div>", unsafe_allow_html=True)

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
                <li>Upload the files using the uploader above and click <strong>“Load &amp; map data”</strong>.</li>
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
    st.markdown("### ⚙️ Controls")
    
    # Reset session button
    st.markdown(
        "<div class='reset-session-hint'>Session</div>",
        unsafe_allow_html=True,
    )
    if st.button("↺ Reset session", key="reset_session_sidebar", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    
    st.markdown("---")

    st.markdown(
        "### 🔍 Advanced search <span class='beta-badge'>BETA</span>",
        unsafe_allow_html=True,
    )
    st.caption("Use structured filters for precise slicing. Applies to the next results view.")

    if st.session_state.normalized_data is not None:
        # Structured filters
        drug_filter = st.text_input("Drug name", key="sidebar_drug")
        reaction_filter = st.text_input("Reaction / event", key="sidebar_reaction")

        with st.expander("Demographics", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                age_min = st.number_input(
                    "Min age",
                    min_value=0,
                    max_value=150,
                    value=0,
                    key="sidebar_age_min",
                )
            with c2:
                age_max = st.number_input(
                    "Max age",
                    min_value=0,
                    max_value=150,
                    value=150,
                    key="sidebar_age_max",
                )
            sex_filter = st.selectbox(
                "Sex", ["All", "M", "F"], key="sidebar_sex"
            )
            country_filter = st.text_input("Country", key="sidebar_country")

        with st.expander("Date & seriousness", expanded=False):
            seriousness_filter = st.checkbox("Serious cases only", key="sidebar_serious")

            enable_date = st.checkbox(
                "Filter by date range", key="sidebar_enable_date"
            )
            date_from = None
            date_to = None
            if enable_date:
                c1, c2 = st.columns(2)
                with c1:
                    date_from = st.date_input("From", key="sidebar_date_from")
                with c2:
                    date_to = st.date_input("To", key="sidebar_date_to")

        apply_adv = st.button("Apply advanced filters", use_container_width=True)
        clear_adv = st.button("Clear filters", use_container_width=True)

        if apply_adv:
            filters: Dict = {}
            if drug_filter:
                filters["drug"] = drug_filter
            if reaction_filter:
                filters["reaction"] = reaction_filter
            if age_min > 0:
                filters["age_min"] = age_min
            if age_max < 150:
                filters["age_max"] = age_max
            if sex_filter != "All":
                filters["sex"] = sex_filter
            if country_filter:
                filters["country"] = country_filter
            if seriousness_filter:
                filters["seriousness"] = True
            if enable_date:
                if date_from:
                    filters["date_from"] = date_from.strftime("%Y-%m-%d")
                if date_to:
                    filters["date_to"] = date_to.strftime("%Y-%m-%d")

            is_valid, error_msg = nl_query_parser.validate_filters(filters)
            if not is_valid:
                st.error(error_msg or "Invalid filter combination.")
            elif not filters:
                st.warning("Select at least one filter to apply advanced search.")
            else:
                # Build a friendly text to show in main query box
                parts = []
                if "drug" in filters:
                    parts.append(f"drug {filters['drug']}")
                if "reaction" in filters:
                    parts.append(f"reaction {filters['reaction']}")
                if "sex" in filters:
                    parts.append("women" if filters["sex"] == "F" else "men")
                if "age_min" in filters or "age_max" in filters:
                    if "age_min" in filters and "age_max" in filters:
                        parts.append(f"age {filters['age_min']}-{filters['age_max']}")
                    elif "age_min" in filters:
                        parts.append(f"age {filters['age_min']}+")
                    elif "age_max" in filters:
                        parts.append(f"age up to {filters['age_max']}")
                if "country" in filters:
                    parts.append(f"in {filters['country']}")
                if "date_from" in filters:
                    parts.append(f"since {filters['date_from']}")
                if "date_to" in filters and "date_from" not in filters:
                    parts.append(f"until {filters['date_to']}")
                if filters.get("seriousness"):
                    parts.append("serious cases")

                query_text = (
                    "Show " + " ".join(parts)
                    if parts
                    else nl_query_parser.filters_to_natural_language(filters)
                )

                st.session_state.last_query_text = query_text
                st.session_state.last_filters = filters
                st.session_state.last_query_source = "advanced"
                st.session_state.show_results = True
                st.rerun()

        if clear_adv:
            for k in [
                "sidebar_drug",
                "sidebar_reaction",
                "sidebar_age_min",
                "sidebar_age_max",
                "sidebar_sex",
                "sidebar_country",
                "sidebar_serious",
                "sidebar_date_from",
                "sidebar_date_to",
                "sidebar_enable_date",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.last_filters = None
            st.session_state.show_results = False
            st.rerun()
    else:
        st.info("Upload and load data to enable advanced search.")

    st.markdown("---")
    st.markdown("### ⚛️ Quantum ranking")
    quantum_enabled = st.checkbox(
        "Enable quantum-inspired ranking",
        value=st.session_state.get("quantum_enabled", False),
        help=(
            "Re-rank drug–event pairs using a heuristic inspired by quantum search. "
            "Deterministic, simulator-only in this demo."
        ),
    )
    st.session_state.quantum_enabled = quantum_enabled

    st.markdown("---")
    
    # Usage statistics (admin view)
    if st.checkbox("📊 Show usage statistics", key="show_stats"):
        try:
            stats = analytics.get_usage_stats()
            st.markdown("#### Usage Statistics")
            st.caption(f"Total sessions: {stats['total_sessions']}")
            st.caption(f"Total events: {stats['total_events']}")
            
            if stats.get("events_by_type"):
                st.markdown("**Events by type:**")
                for event_type, count in stats["events_by_type"].items():
                    st.caption(f"  • {event_type}: {count}")
        except Exception:
            st.info("Usage statistics not available")
    
    st.markdown("---")
    st.caption("AetherSignal – Quantum PV Explorer (demo build)")
    st.caption("Exploratory only – not for regulatory decision-making.")
