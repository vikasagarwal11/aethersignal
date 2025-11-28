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
from src import quantum_anomaly
from src import quantum_clustering
from src import llm_explain
from src.app_helpers import (
    cached_get_summary_stats,
    format_reaction_with_meddra,
    render_filter_chips,
)
from src.ui.drill_down import (
    render_drill_down_table,
    render_case_details,
    render_drug_reaction_drill_down,
)
from src.e2b_export import export_to_e2b, validate_e2b_xml
from src.time_to_onset import calculate_time_to_onset, fit_weibull, get_tto_distribution, analyze_drug_reaction_tto
from src.ui.case_series_viewer import render_case_series_viewer
from src.case_processing import (
    analyze_dechallenge_rechallenge,
    analyze_dose_event_relationship,
    analyze_therapy_duration,
    analyze_indication_vs_reaction,
    analyze_reporter_type,
    analyze_outcomes_breakdown,
    detect_duplicate_cases,
)
from src.signal_prioritization import (
    calculate_signal_prioritization_score,
    calculate_rag_score,
)
from src.literature_integration import enrich_signal_with_literature
from src.longitudinal_spike import detect_spikes, detect_statistical_spikes, analyze_trend_changepoint
from src.new_signal_detection import calculate_unexpectedness_score, detect_new_signals
from src.class_effect_detection import detect_class_effects, analyze_drug_class_signal
from src.exposure_normalization import normalize_by_exposure, calculate_incidence_rate
from src.quantum_explainability import (
    explain_quantum_ranking,
    explain_quantum_clustering,
    generate_quantum_circuit_diagram
)
from src.quantum_duplicate_detection import (
    detect_duplicates_quantum,
    compare_classical_vs_quantum_duplicates
)
from src.utils import normalize_text, safe_divide


def _log_perf_event(label: str, duration: float, extra: Optional[Dict] = None) -> None:
    if not st.session_state.get("analytics_enabled"):
        return
    payload = {"label": label, "duration_ms": round(duration * 1000, 2)}
    if extra:
        payload.update(extra)
    analytics.log_event("perf_metric", payload)


def _render_signal_card(
    drug: str,
    reaction: str,
    prr_ror: Dict,
    ic: Dict,
    bcpnn: Dict,
    ebgm: Optional[Dict],
    a: int,
    b: int,
    c: int,
    d: int,
    signal_strength: str,
    signal_color: str,
) -> None:
    """
    Render a compact signal card with traffic-light styling and 2x2 counts.
    """
    if not prr_ror:
        return

    prr_val = prr_ror.get("prr", 0.0)
    ror_val = prr_ror.get("ror", 0.0)
    ic_val = ic.get("ic", 0.0) if ic else 0.0
    bcpnn_val = bcpnn.get("ic", 0.0) if bcpnn else 0.0
    ebgm_val = ebgm.get("ebgm", 0.0) if ebgm else None

    ebgm_text = f", EBGM {ebgm_val:.2f}" if ebgm_val is not None else ""

    st.markdown(
        f"""
<div class="signal-card" style="
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    border-left: 4px solid {signal_color};
    background: #f8fafc;
    box-shadow: 0 3px 10px rgba(15,23,42,0.08);
    max-width: 960px;
">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
    <div style="flex:1;">
      <div style="font-size:0.9rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.2rem;">
        Signal overview
      </div>
      <div style="font-size:1.05rem; font-weight:600; color:#0f172a;">
        {drug} &mdash; {reaction}
      </div>
      <div style="margin-top:0.35rem; font-size:0.85rem; color:#475569;">
        <span style="font-weight:600; color:{signal_color};">{signal_strength} signal</span>
        &nbsp;&middot;&nbsp;
        PRR {prr_val:.2f}, ROR {ror_val:.2f}, IC {ic_val:.2f}, BCPNN {bcpnn_val:.2f}{ebgm_text}
      </div>
    </div>
    <div style="flex:0 0 220px; font-size:0.8rem; color:#0f172a; background:white; border-radius:10px; padding:0.5rem 0.75rem; border:1px solid #e2e8f0;">
      <div style="font-weight:600; margin-bottom:0.25rem; color:#334155;">
        2×2 exposure&nbsp;/&nbsp;event table
      </div>
      <table style="width:100%; border-collapse:collapse; font-size:0.78rem;">
        <thead>
          <tr>
            <th style="text-align:left; padding:2px 4px; border-bottom:1px solid #e2e8f0;"></th>
            <th style="text-align:right; padding:2px 4px; border-bottom:1px solid #e2e8f0;">Drug</th>
            <th style="text-align:right; padding:2px 4px; border-bottom:1px solid #e2e8f0;">No drug</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:2px 4px; color:#475569;">Reaction</td>
            <td style="padding:2px 4px; text-align:right;">{int(a):,}</td>
            <td style="padding:2px 4px; text-align:right;">{int(c):,}</td>
          </tr>
          <tr>
            <td style="padding:2px 4px; color:#475569;">No reaction</td>
            <td style="padding:2px 4px; text-align:right;">{int(b):,}</td>
            <td style="padding:2px 4px; text-align:right;">{int(d):,}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


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

    # Show query method and confidence (if available)
    query_method = st.session_state.get("last_query_method")
    query_confidence = st.session_state.get("last_query_confidence")
    if query_method:
        method_label = "🤖 AI-enhanced" if query_method == "llm_fallback" else "⚙️ Rule-based"
        confidence_pct = int(query_confidence * 100) if query_confidence else 100
        st.caption(f"{method_label} parsing (confidence: {confidence_pct}%)")
    
    # Show AND/OR logic indicator for multiple reactions
    if "reaction" in filters and isinstance(filters.get("reaction"), list) and len(filters.get("reaction", [])) > 1:
        reaction_logic = filters.get("reaction_logic", "OR")
        reactions_list = filters["reaction"]
        logic_icon = "🔗" if reaction_logic == "AND" else "🔀"
        logic_text = "ALL" if reaction_logic == "AND" else "ANY"
        st.info(
            f"{logic_icon} **Multiple reactions detected:** Showing cases with {logic_text} of: "
            f"{', '.join(reactions_list[:3])}{'...' if len(reactions_list) > 3 else ''}"
        )
    
    # Track query execution
    if st.session_state.get("analytics_enabled"):
        analytics.log_event(
            "query_executed",
            {
                "source": source,
                "has_drug": "drug" in filters,
                "has_reaction": "reaction" in filters,
                "reaction_logic": filters.get("reaction_logic", "OR"),
                "quantum_enabled": st.session_state.get("quantum_enabled", False),
            },
        )
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

    # Lightweight conversational-style answer (rule-based, no LLM required)
    try:
        drug_txt = filters.get("drug") if isinstance(filters.get("drug"), str) else None
        react_txt = filters.get("reaction") if isinstance(filters.get("reaction"), str) else None
        short_bits = []
        # Add provenance: "Based on X matching cases in your uploaded data..."
        short_bits.append(f"Based on {summary['matching_cases']:,} matching cases in your uploaded data (out of {summary['total_cases']:,} total, {summary['percentage']:.2f}%).")
        if drug_txt:
            short_bits.append(f"Drug: {drug_txt}.")
        if react_txt:
            short_bits.append(f"Reaction: {react_txt}.")
        if summary.get("serious_count") is not None:
            short_bits.append(f"Serious cases: {summary['serious_count']:,} ({summary.get('serious_percentage', 0):.1f}%).")
        short_answer = " ".join(short_bits)
        st.markdown(
            f"<div class='block-card' style='margin-bottom:12px;'><strong>💬 Answer:</strong> {short_answer}</div>",
            unsafe_allow_html=True,
        )
    except Exception:
        pass

    # Audit logging for queries (after summary is available)
    try:
        from src.audit_trail import log_audit_event
        log_audit_event(
            event="query_executed",
            details={
                "query": query_text[:100] if query_text else "",
                "filters": {k: str(v)[:50] for k, v in filters.items()},
                "source": source,
                "matching_cases": summary.get("matching_cases", len(filtered_df)),
            }
        )
    except Exception:
        pass  # Silently fail

    # Add conversational response tab if LLM is enabled
    use_llm = st.session_state.get("use_llm", False)
    if use_llm:
        overview_tab, conversational_tab, signals_tab, trends_tab, cases_tab, report_tab = st.tabs(
            ["📊 Overview", "💬 Conversational", "⚛️ Signals", "📅 Time & Co-reactions", "📋 Cases", "📄 Report"]
        )
    else:
        overview_tab, signals_tab, trends_tab, cases_tab, report_tab = st.tabs(
            ["📊 Overview", "⚛️ Signals", "📅 Time & Co-reactions", "📋 Cases", "📄 Report"]
        )
        conversational_tab = None  # Not available

    # ---------------- Overview Tab ----------------
    with overview_tab:
        _render_overview_tab(filters, source_label, summary, filtered_df, normalized_df)

    # ---------------- Conversational Tab (if LLM enabled) ----------------
    if conversational_tab is not None:
        with conversational_tab:
            _render_conversational_tab(filters, query_text, summary, filtered_df, normalized_df)

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

    # Top drugs / reactions with drill-down
    if summary.get("top_drugs") or summary.get("top_reactions"):
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if summary.get("top_drugs"):
            with c1:
                st.markdown("#### 💊 Top drugs")
                st.caption("💡 Select a drug to see detailed cases")
                td_df = pd.DataFrame(
                    list(summary["top_drugs"].items()), columns=["Drug", "Count"]
                )
                
                # Use drill-down component
                selected_drug = render_drill_down_table(
                    td_df,
                    filtered_df,
                    "top_drugs",
                    "Drug",
                )
                
                # Show detailed cases if drug selected
                if selected_drug:
                    # Extract actual drug name (remove MedDRA PT if present)
                    actual_drug = selected_drug.split(" (MedDRA")[0].strip()
                    render_case_details(
                        filtered_df,
                        actual_drug,
                        "drug_name",
                        "Drug",
                        max_cases=100,
                    )
        
        if summary.get("top_reactions"):
            with c2:
                st.markdown("#### ⚠️ Top reactions")
                st.caption("💡 Select a reaction to see detailed cases")
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
                        "Count": count,
                        "Original": reaction,  # Keep original for filtering
                    })
                
                tr_df = pd.DataFrame(reactions_data)
                
                # Use drill-down component
                selected_reaction_display = render_drill_down_table(
                    tr_df[["Reaction", "Count"]],  # Show only display columns
                    filtered_df,
                    "top_reactions",
                    "Reaction",
                )
                
                # Show detailed cases if reaction selected
                if selected_reaction_display:
                    # Find original reaction name
                    selected_row = tr_df[tr_df["Reaction"] == selected_reaction_display]
                    if not selected_row.empty:
                        original_reaction = selected_row.iloc[0]["Original"]
                        render_case_details(
                            filtered_df,
                            original_reaction,
                            "reaction",
                            "Reaction",
                            max_cases=100,
                        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Case Processing Summary
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("📊 Case Processing Summary")
    
    col1, col2, col3 = st.columns(3)
    
    # Reporter Type
    with col1:
        reporter_analysis = analyze_reporter_type(filtered_df)
        if reporter_analysis['reporter_types']:
            st.markdown("**👤 Reporter Types**")
            reporter_df = pd.DataFrame(list(reporter_analysis['reporter_types'].items()), columns=['Type', 'Count'])
            st.dataframe(reporter_df, use_container_width=True, hide_index=True)
        else:
            st.info("No reporter type data available")
    
    # Outcomes Breakdown
    with col2:
        outcomes_analysis = analyze_outcomes_breakdown(filtered_df)
        if outcomes_analysis['outcomes']:
            st.markdown("**📈 Outcomes Breakdown**")
            outcomes_df = pd.DataFrame(list(outcomes_analysis['outcomes'].items()), columns=['Outcome', 'Count'])
            st.dataframe(outcomes_df, use_container_width=True, hide_index=True)
        else:
            st.info("No outcome data available")
    
    # Duplicate Detection (Quantum-Enhanced)
    with col3:
        st.markdown("**🔍 Data Quality**")
        
        # Quick drug normalization button
        if "drug_name" in filtered_df.columns:
            if st.button("✨ Normalize Drug Names", key="normalize_drugs_quick", use_container_width=True):
                try:
                    from src.drug_name_normalization import normalize_drug_column, group_similar_drugs
                    
                    with st.spinner("Normalizing drug names in filtered data..."):
                        normalized_filtered = normalize_drug_column(filtered_df.copy(), drug_column='drug_name')
                        grouped_filtered = group_similar_drugs(normalized_filtered, drug_column='drug_name', threshold=0.85)
                        
                        # Update the filtered dataframe
                        if 'drug_name_normalized' in grouped_filtered.columns:
                            grouped_filtered['drug_name'] = grouped_filtered['drug_name_normalized']
                            grouped_filtered = grouped_filtered.drop(columns=['drug_name_normalized'])
                        
                        # Update session state
                        if st.session_state.get('normalized_data') is not None:
                            # Update the main normalized data
                            main_normalized = normalize_drug_column(st.session_state.normalized_data.copy(), drug_column='drug_name')
                            main_grouped = group_similar_drugs(main_normalized, drug_column='drug_name', threshold=0.85)
                            st.session_state.normalized_data = main_grouped
                            st.session_state.data = main_grouped
                        
                        st.success("✅ Drug names normalized! Refresh to see updated results.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # Compare classical vs quantum
        duplicate_comparison = compare_classical_vs_quantum_duplicates(filtered_df)
        classical_result = duplicate_comparison['classical']
        quantum_result = duplicate_comparison['quantum']
        
        st.metric("Unique Cases", f"{classical_result['unique_cases']:,}")
        st.metric("Duplicate Cases", f"{quantum_result['duplicate_cases']:,}")
        
        if quantum_result['duplicate_cases'] > 0:
            st.warning(f"⚠️ {quantum_result['duplicate_rate']:.1f}% duplicate rate")
            
            # Show quantum advantage if applicable
            if duplicate_comparison['comparison']['quantum_finds_more']:
                diff = duplicate_comparison['comparison']['difference']
                st.info(f"⚛️ Quantum method found {diff} additional duplicate(s)")
        else:
            st.success("✅ No duplicates detected")
        
        # Quantum duplicate details
        with st.expander("⚛️ Quantum Duplicate Detection Details", expanded=False):
            st.caption("Quantum-inspired hashing and distance metrics for enhanced duplicate detection")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Classical Method**")
                st.write(f"- Duplicates: {classical_result.get('duplicate_cases', 0)}")
                st.write(f"- Rate: {classical_result.get('duplicate_rate', 0):.1f}%")
            
            with col2:
                st.markdown("**Quantum Method**")
                st.write(f"- Duplicates: {quantum_result.get('duplicate_cases', 0)}")
                st.write(f"- Exact: {quantum_result.get('exact_duplicates', 0)}")
                st.write(f"- Fuzzy: {quantum_result.get('fuzzy_duplicates', 0)}")
                st.write(f"- Rate: {quantum_result.get('duplicate_rate', 0):.1f}%")
            
            if quantum_result.get('duplicate_groups'):
                st.markdown("**Duplicate Groups (Top 5):**")
                for group in quantum_result['duplicate_groups'][:5]:
                    st.write(f"- Group: {group['count']} cases (Hash: {str(group['hash'])[:16]}...)")
    
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


def _render_conversational_tab(
    filters: Dict,
    query_text: str,
    summary: Dict,
    filtered_df: pd.DataFrame,
    normalized_df: pd.DataFrame
):
    """Render conversational response tab with AI-generated insights."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("💬 Conversational Response")
    st.caption("AI-generated natural language interpretation of your query results")
    
    try:
        from src.ai.conversational_engine import process_conversational_query
        
        use_llm = st.session_state.get("use_llm", False)
        result = process_conversational_query(query_text, normalized_df, use_llm=use_llm)
        
        # Display response
        st.markdown("### 📝 Response")
        st.markdown(result.get("response", "Unable to generate response."))
        
        # Show red flags if any
        red_flags = result.get("red_flags", [])
        if red_flags:
            st.markdown("---")
            st.markdown("### ⚠️ Red Flags")
            for flag in red_flags:
                st.warning(f"• {flag}")
        
        # Show trends
        trends = result.get("trends", {})
        if trends.get("has_trend"):
            st.markdown("---")
            st.markdown("### 📈 Trends")
            if trends.get("direction"):
                direction_icon = "📈" if trends["direction"] == "increasing" else "📉" if trends["direction"] == "decreasing" else "➡️"
                st.info(f"{direction_icon} Trend: {trends['direction'].title()}")
            if trends.get("spikes"):
                st.info(f"🔍 Detected {len(trends['spikes'])} significant spike(s)")
        
        # Option to generate comprehensive summary
        if "drug" in filters and "reaction" in filters:
            st.markdown("---")
            if st.button("📊 Generate Comprehensive Signal Summary", use_container_width=True):
                with st.spinner("Generating comprehensive summary..."):
                    try:
                        from src.ai.signal_summarizer import generate_comprehensive_summary
                        drug = filters["drug"] if isinstance(filters["drug"], str) else filters["drug"][0]
                        reaction = filters["reaction"] if isinstance(filters["reaction"], str) else filters["reaction"][0]
                        prr_ror = result.get("prr_ror")
                        
                        summary_text = generate_comprehensive_summary(
                            drug, reaction, summary, prr_ror, trends, use_llm=use_llm
                        )
                        st.markdown("### 📋 Comprehensive Summary")
                        st.markdown(summary_text)
                        
                        # Add causal explanation if LLM enabled
                        if use_llm:
                            st.markdown("---")
                            if st.button("🧠 Generate Causal Explanation", use_container_width=True):
                                with st.spinner("Analyzing mechanisms..."):
                                    try:
                                        from src.ai.signal_summarizer import generate_causal_explanation
                                        causal_explanation = generate_causal_explanation(
                                            drug, reaction, prr_ror, summary
                                        )
                                        if causal_explanation:
                                            st.markdown("### ⚗️ Causal Reasoning")
                                            st.markdown(causal_explanation)
                                        else:
                                            st.info("Unable to generate causal explanation. This may require specialized models (Claude Opus).")
                                    except Exception as e:
                                        st.error(f"Error generating causal explanation: {str(e)}")
                    except Exception as e:
                        st.error(f"Error generating summary: {str(e)}")
    
    except ImportError:
        st.info("💡 Conversational features require AI modules. Enable AI-enhanced query interpretation in query settings.")
    except Exception as e:
        st.error(f"Error generating conversational response: {str(e)}")
    
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
                    # Add richer narrative using seriousness, demographics, and trend (if available)
                    extra_bits = []
                    matching_cases = summary.get("matching_cases")
                    serious_pct = summary.get("serious_percentage")
                    if matching_cases:
                        if serious_pct is not None:
                            extra_bits.append(
                                f"Among {matching_cases:,} matching cases, about {serious_pct:.1f}% are marked serious."
                            )
                        else:
                            extra_bits.append(f"This signal is based on {matching_cases:,} matching cases.")
                    age_stats = summary.get("age_stats") or {}
                    median_age = age_stats.get("median")
                    if median_age is not None:
                        extra_bits.append(f"The median patient age in this subset is around {median_age:.0f} years.")
                    sex_dist = summary.get("sex_distribution") or {}
                    if sex_dist:
                        top_sex = max(sex_dist.items(), key=lambda x: x[1])[0]
                        extra_bits.append(f"Most reports are in patients with sex coded as '{top_sex}'.")
                    trend = summary.get("time_trend") or {}
                    trend_summary = None
                    if trend and len(trend) >= 2:
                        # Compare latest vs prior period in the same way as the Trends tab
                        try:
                            trend_items = sorted(
                                ((pd.Period(k), v) for k, v in trend.items()),
                                key=lambda kv: kv[0],
                            )
                            latest_period, latest_count = trend_items[-1]
                            prev_period, prev_count = trend_items[-2]
                            if prev_count:
                                delta = latest_count - prev_count
                                pct = safe_divide(delta, prev_count, 0) * 100
                                direction = "higher" if delta > 0 else "lower" if delta < 0 else "similar"
                                trend_summary = (
                                    f"Recent period ({latest_period.strftime('%b %Y')}) has {latest_count} cases, "
                                    f"{abs(pct):.1f}% {direction} than {prev_period.strftime('%b %Y')}."
                                )
                                extra_bits.append(trend_summary)
                        except Exception:
                            trend_summary = None
                    if extra_bits:
                        st.info(" ".join(extra_bits))

                    # Optional AI-assisted explanation using external LLM (if configured)
                    with st.expander("AI-assisted explanation (requires external LLM)", expanded=False):
                        if not llm_explain.has_llm_configured():
                            st.caption(
                                "To enable this, set an OPENAI_API_KEY environment variable and "
                                "install the 'openai' Python client in your environment. "
                                "No external calls are made unless you click the button below."
                            )
                        else:
                            if st.button("Generate AI explanation", type="secondary", use_container_width=True):
                                with st.spinner("Contacting external LLM for a richer explanation..."):
                                    context = {
                                        "drug": drug,
                                        "reaction": reaction,
                                        "a": int(a),
                                        "b": int(b),
                                        "c": int(c),
                                        "d": int(d),
                                        "prr": prr_ror.get("prr"),
                                        "ror": prr_ror.get("ror"),
                                        "ic": ic.get("ic") if ic else None,
                                        "bcpnn": bcpnn.get("ic") if bcpnn else None,
                                        "ebgm": ebgm.get("ebgm") if ebgm else None,
                                        "serious_pct": serious_pct,
                                        "matching_cases": matching_cases,
                                        "median_age": median_age,
                                        "sex_distribution": sex_dist,
                                        "top_countries": (summary.get("country_distribution") or {}),
                                        "trend_summary": trend_summary,
                                    }
                                    llm_text = llm_explain.generate_signal_explanation(context)
                                    if llm_text:
                                        st.markdown(llm_text)
                                    else:
                                        st.info("No AI explanation could be generated. Check API configuration if needed.")
                
                # Signal Prioritization Score (SPS) and RAG
                if prr_ror and summary['matching_cases'] >= 3:
                    st.markdown("---")
                    st.subheader("🎯 Signal Prioritization")
                    
                    # Get IC and EBGM for SPS calculation
                    from src.advanced_stats import calculate_ic, calculate_ebgm
                    ic_result = calculate_ic(a, b, c, d)
                    ebgm_result = calculate_ebgm(a, b, c, d)
                    
                    # Calculate SPS
                    sps_result = calculate_signal_prioritization_score(
                        drug, reaction, filtered_df,
                        prr=prr_val, ror=ror_val,
                        ic=ic_result.get('ic'), ebgm=ebgm_result.get('ebgm'),
                        case_count=summary['matching_cases']
                    )
                    
                    # Calculate RAG
                    statistical_strength = min(100, (prr_val / 5) * 50 if prr_val > 0 else 0)  # Scale PRR to 0-100
                    clinical_seriousness = min(100, (summary.get('serious_percentage', 0) / 100) * 100)
                    rag_result = calculate_rag_score(statistical_strength, clinical_seriousness)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Signal Prioritization Score (SPS)**")
                        sps_score = sps_result.get('sps_score', 0)
                        sps_rank = sps_result.get('sps_rank', 'Low')
                        rank_colors = {
                            'Critical': '#dc2626',
                            'High': '#ea580c',
                            'Medium': '#f59e0b',
                            'Low': '#84cc16'
                        }
                        st.markdown(
                            f"<div style='font-size:2rem; font-weight:bold; color:{rank_colors.get(sps_rank, '#64748b')}'>"
                            f"{sps_score:.1f}/100</div>",
                            unsafe_allow_html=True
                        )
                        st.caption(f"Priority: **{sps_rank}**")
                        
                        # Show components
                        components = sps_result.get('components', {})
                        if components:
                            with st.expander("SPS Components", expanded=False):
                                for comp_name, comp_score in components.items():
                                    st.write(f"**{comp_name.replace('_', ' ').title()}:** {comp_score:.1f} points")
                    
                    with col2:
                        st.markdown("**Risk Assessment Grid (RAG)**")
                        rag_quadrant = rag_result.get('quadrant', '')
                        rag_priority = rag_result.get('priority', 'Medium')
                        st.markdown(
                            f"<div style='font-size:1.2rem; font-weight:600; color:{rank_colors.get(rag_priority, '#64748b')}'>"
                            f"{rag_quadrant}</div>",
                            unsafe_allow_html=True
                        )
                        st.caption(f"Priority: **{rag_priority}**")
                        st.write(f"**Statistical Strength:** {rag_result.get('statistical_strength', 0):.1f}/100")
                        st.write(f"**Clinical Seriousness:** {rag_result.get('clinical_seriousness', 0):.1f}/100")
                
                # Case Processing Analysis
                if prr_ror and summary['matching_cases'] >= 3:
                    st.markdown("---")
                    st.subheader("🔬 Case Processing Analysis")
                    
                    # Filter for drug-reaction pair
                    dr_filtered = filtered_df.copy()
                    if 'drug_name' in dr_filtered.columns:
                        dr_filtered = dr_filtered[dr_filtered['drug_name'].astype(str).str.contains(str(drug), case=False, na=False)]
                    if 'reaction' in dr_filtered.columns:
                        dr_filtered = dr_filtered[dr_filtered['reaction'].astype(str).str.contains(str(reaction), case=False, na=False)]
                    
                    if not dr_filtered.empty:
                        # Dechallenge/Rechallenge
                        dechal_rechal = analyze_dechallenge_rechallenge(dr_filtered)
                        if dechal_rechal['total_cases'] > 0:
                            with st.expander("🔄 Dechallenge/Rechallenge Analysis", expanded=True):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**Dechallenge**")
                                    st.write(f"✅ Positive: {dechal_rechal['dechallenge_positive']}")
                                    st.write(f"❌ Negative: {dechal_rechal['dechallenge_negative']}")
                                    st.write(f"❓ Unknown: {dechal_rechal['dechallenge_unknown']}")
                                    if dechal_rechal['positive_dechallenge_rate'] > 0:
                                        st.metric("Positive Rate", f"{dechal_rechal['positive_dechallenge_rate']:.1f}%")
                                with col2:
                                    st.markdown("**Rechallenge**")
                                    st.write(f"✅ Positive: {dechal_rechal['rechallenge_positive']}")
                                    st.write(f"❌ Negative: {dechal_rechal['rechallenge_negative']}")
                                    st.write(f"❓ Unknown: {dechal_rechal['rechallenge_unknown']}")
                                    if dechal_rechal['positive_rechallenge_rate'] > 0:
                                        st.metric("Positive Rate", f"{dechal_rechal['positive_rechallenge_rate']:.1f}%")
                        
                        # Dose-Event Relationship
                        dose_analysis = analyze_dose_event_relationship(dr_filtered, drug, reaction)
                        if dose_analysis['cases_with_dose'] > 0:
                            with st.expander("💊 Dose-Event Relationship", expanded=False):
                                if dose_analysis['dose_statistics']:
                                    stats = dose_analysis['dose_statistics']
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Mean Dose", f"{stats.get('mean', 0):.2f}")
                                    with col2:
                                        st.metric("Median Dose", f"{stats.get('median', 0):.2f}")
                                    with col3:
                                        st.metric("Min Dose", f"{stats.get('min', 0):.2f}")
                                    with col4:
                                        st.metric("Max Dose", f"{stats.get('max', 0):.2f}")
                                
                                if dose_analysis['dose_units']:
                                    st.write("**Dose Units Distribution:**")
                                    st.dataframe(pd.DataFrame(list(dose_analysis['dose_units'].items()), columns=['Unit', 'Count']), use_container_width=True, hide_index=True)
                                
                                if dose_analysis['dose_forms']:
                                    st.write("**Dose Forms Distribution:**")
                                    st.dataframe(pd.DataFrame(list(dose_analysis['dose_forms'].items()), columns=['Form', 'Count']), use_container_width=True, hide_index=True)
                        
                        # Therapy Duration
                        therapy_analysis = analyze_therapy_duration(dr_filtered, drug)
                        if therapy_analysis['cases_with_duration'] > 0:
                            with st.expander("⏱️ Therapy Duration Analysis", expanded=False):
                                if therapy_analysis['duration_statistics']:
                                    stats = therapy_analysis['duration_statistics']
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Mean Duration", f"{stats.get('mean_days', 0):.1f} days")
                                        st.caption(f"({stats.get('mean_weeks', 0):.1f} weeks)")
                                    with col2:
                                        st.metric("Median Duration", f"{stats.get('median_days', 0):.1f} days")
                                    with col3:
                                        st.metric("Range", f"{stats.get('min_days', 0):.0f} - {stats.get('max_days', 0):.0f} days")
                        
                        # Indication vs Reaction
                        indication_analysis = analyze_indication_vs_reaction(dr_filtered)
                        if indication_analysis['cases_with_indication'] > 0:
                            with st.expander("📋 Indication vs Reaction Analysis", expanded=False):
                                if indication_analysis['top_indications']:
                                    st.write("**Top Indications:**")
                                    ind_df = pd.DataFrame(list(indication_analysis['top_indications'].items()), columns=['Indication', 'Count'])
                                    st.dataframe(ind_df, use_container_width=True, hide_index=True)
                                
                                if indication_analysis['indication_reaction_pairs']:
                                    st.write("**Common Indication → Reaction Pairs:**")
                                    pair_df = pd.DataFrame(list(indication_analysis['indication_reaction_pairs'].items()), columns=['Pair', 'Count'])
                                    st.dataframe(pair_df.head(10), use_container_width=True, hide_index=True)
                        
                        # Literature Evidence
                        with st.expander("📚 Literature Evidence", expanded=False):
                            use_llm = st.session_state.get("use_llm", False)
                            if st.button("🔍 Search Literature", key="search_literature", use_container_width=True):
                                with st.spinner("Searching PubMed and ClinicalTrials.gov..."):
                                    # Use enhanced literature if LLM enabled
                                    if use_llm:
                                        from src.ai.literature_enhancer import enrich_signal_with_enhanced_literature
                                        literature = enrich_signal_with_enhanced_literature(drug, reaction, use_llm=True)
                                    else:
                                        from src.literature_integration import enrich_signal_with_literature
                                        literature = enrich_signal_with_literature(drug, reaction)
                                    
                                    if literature['total_pubmed'] > 0 or literature['total_trials'] > 0:
                                        # Show LLM insights if available
                                        if use_llm and literature.get('key_findings'):
                                            st.markdown("**🔍 AI-Generated Insights**")
                                            with st.expander("📊 Key Findings Across Papers", expanded=True):
                                                st.write(literature['key_findings'])
                                            
                                            if literature.get('mechanisms'):
                                                with st.expander("⚗️ Proposed Mechanisms", expanded=False):
                                                    st.write(literature['mechanisms'])
                                            
                                            if literature.get('consensus'):
                                                with st.expander("🎯 Consensus View", expanded=False):
                                                    st.write(literature['consensus'])
                                            
                                            st.markdown("---")
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("**📄 PubMed Articles**")
                                            if literature['pubmed_articles']:
                                                for article in literature['pubmed_articles']:
                                                    st.markdown(
                                                        f"**{article.get('title', 'N/A')}**  \n"
                                                        f"*{article.get('authors', 'N/A')}*  \n"
                                                        f"{article.get('journal', '')} ({article.get('year', 'N/A')})  \n"
                                                        f"[View on PubMed]({article.get('url', '#')})"
                                                    )
                                                    
                                                    # Show LLM summary if available
                                                    if use_llm and literature.get('llm_summaries'):
                                                        for summary_item in literature['llm_summaries']:
                                                            if summary_item.get('pmid') == article.get('pmid') and summary_item.get('summary'):
                                                                with st.expander("🤖 AI Summary", expanded=False):
                                                                    st.write(summary_item['summary'])
                                                    
                                                    if article.get('abstract'):
                                                        with st.expander("Abstract", expanded=False):
                                                            st.write(article['abstract'])
                                                    st.markdown("---")
                                            else:
                                                st.info("No PubMed articles found")
                                        
                                        with col2:
                                            st.markdown("**🧪 Clinical Trials**")
                                            if literature['clinical_trials']:
                                                for trial in literature['clinical_trials']:
                                                    st.markdown(
                                                        f"**{trial.get('title', 'N/A')}**  \n"
                                                        f"Status: {trial.get('status', 'N/A')}  \n"
                                                        f"Phase: {', '.join(trial.get('phase', []))}  \n"
                                                        f"[View on ClinicalTrials.gov]({trial.get('url', '#')})"
                                                    )
                                                    st.markdown("---")
                                            else:
                                                st.info("No clinical trials found")
                                    else:
                                        st.info("No literature evidence found for this drug-reaction pair")
                            else:
                                st.caption("Click the button above to search PubMed and ClinicalTrials.gov for literature evidence")
                        
                        # New Signal Detection (Unexpectedness)
                        with st.expander("🆕 New Signal Detection", expanded=False):
                            st.caption("Identifies novel or unexpected drug-reaction signals")
                            unexpectedness = calculate_unexpectedness_score(drug, reaction, normalized_df)
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Unexpectedness", f"{unexpectedness['unexpectedness_score']:.1f}/100")
                            with col2:
                                st.metric("Novelty", f"{unexpectedness['novelty_score']:.1f}/100")
                            with col3:
                                st.metric("Frequency", f"{unexpectedness['frequency_score']:.1f}/100")
                            with col4:
                                st.metric("Rarity", f"{unexpectedness['rarity_score']:.1f}/100")
                            
                            if unexpectedness['is_novel']:
                                st.success("✅ Novel drug-reaction combination")
                            if unexpectedness['is_rare']:
                                st.warning("⚠️ Rare reaction (<1% prevalence)")
                            
                            st.write(f"**Explanation:** {unexpectedness['explanation']}")
                            
                            if unexpectedness['other_drugs_with_reaction'] > 0:
                                st.info(f"ℹ️ {unexpectedness['other_drugs_with_reaction']} other drug(s) also show this reaction")
                        
                        # Class Effect Detection
                        with st.expander("💊 Class Effect Detection", expanded=False):
                            st.caption("Checks if this signal is part of a drug class pattern")
                            class_analysis = analyze_drug_class_signal(normalized_df, drug, reaction)
                            
                            if class_analysis['is_class_effect']:
                                st.warning(f"⚠️ **Class Effect Detected:** {class_analysis['drug_class']}")
                                st.write(f"**Class Effect Strength:** {class_analysis['class_effect_strength']:.1%}")
                                st.write(f"**Other drugs in class showing this reaction:** {class_analysis['n_other_drugs_showing']}")
                                
                                if class_analysis['other_drugs_showing_reaction']:
                                    other_drugs_df = pd.DataFrame(class_analysis['other_drugs_showing_reaction'])
                                    st.dataframe(other_drugs_df, use_container_width=True, hide_index=True)
                            else:
                                if class_analysis['drug_class']:
                                    st.info(f"ℹ️ Drug belongs to class '{class_analysis['drug_class']}', but no class effect detected")
                                else:
                                    st.info("ℹ️ No known drug class identified for this drug")
                        
                        # Exposure Normalization
                        with st.expander("📊 Exposure Normalization", expanded=False):
                            st.caption("Adjusts signal metrics for drug exposure rates")
                            exposure_normalized = normalize_by_exposure(drug, reaction, normalized_df)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Cases/Million Exposures", f"{exposure_normalized['cases_per_million_exposures']:.2f}")
                            with col2:
                                st.metric("Exposure Ratio", f"{exposure_normalized['exposure_ratio']:.2%}")
                            with col3:
                                st.metric("Normalized PRR", f"{exposure_normalized['normalized_prr']:.2f}")
                            
                            st.caption(f"**Drug Exposure:** {exposure_normalized['drug_exposure']:,.0f} | **Total Exposure:** {exposure_normalized['total_exposure']:,.0f}")
                            st.caption(f"**Background Rate:** {exposure_normalized['background_rate']:.4f} | **Crude PRR:** {exposure_normalized['crude_prr']:.2f}")
                            
                            st.info("💡 Note: Exposure data is estimated from case counts. For accurate normalization, provide prescription/patient exposure data.")
                
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
                    
                    # IC, BCPNN, EBGM
                    ic = advanced_stats.calculate_ic(a, b, c, d)
                    bcpnn = advanced_stats.calculate_bcpnn(a, b, c, d)
                    ebgm = advanced_stats.calculate_ebgm(a, b, c, d)
                    
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

                    # Compact signal card summary
                    _render_signal_card(
                        drug=drug,
                        reaction=reaction,
                        prr_ror=prr_ror,
                        ic=ic,
                        bcpnn=bcpnn,
                        ebgm=ebgm,
                        a=a,
                        b=b,
                        c=c,
                        d=d,
                        signal_strength=signal_strength,
                        signal_color=signal_color,
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

                    # 2x2 contingency table viewer
                    st.markdown("#### 2×2 exposure–event table")
                    cont_df = pd.DataFrame(
                        [
                            {"Reaction": "Yes", "Drug": int(a), "No drug": int(c)},
                            {"Reaction": "No", "Drug": int(b), "No drug": int(d)},
                        ]
                    ).set_index("Reaction")
                    st.dataframe(cont_df, use_container_width=True)
                    
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
                    
                    # Quantum-Inspired Clustering
                    matching_cases = summary.get("matching_cases", 0)
                    if matching_cases >= 20:  # Minimum cases for clustering
                        st.markdown("---")
                        st.markdown("#### ⚛️ Quantum-Inspired Clustering (experimental)")
                        st.caption(
                            "Unsupervised clustering of cases within this signal to discover "
                            "high-risk patient subgroups. Uses quantum-inspired distance weighting."
                        )
                        
                        with st.spinner("Clustering cases with quantum-inspired algorithm..."):
                            clusters = quantum_clustering.cluster_cases_for_signal(
                                normalized_df, drug, reaction, min_cases=20, k=3
                            )
                        
                        if clusters:
                            cluster_data = []
                            for cluster in clusters:
                                cluster_data.append({
                                    "Cluster": f"Cluster {cluster['cluster_id']}",
                                    "Cases": cluster['size'],
                                    "Mean Age": f"{cluster['mean_age']:.1f}" if cluster['mean_age'] is not None else "N/A",
                                    "Serious %": f"{cluster['serious_pct']:.1f}%",
                                    "Male %": f"{cluster['male_pct']:.1f}%" if cluster['male_pct'] is not None else "N/A",
                                    "Female %": f"{cluster['female_pct']:.1f}%" if cluster['female_pct'] is not None else "N/A",
                                })
                            
                            cluster_df = pd.DataFrame(cluster_data)
                            st.dataframe(cluster_df, use_container_width=True, hide_index=True)
                            
                            # Highlight highest-risk cluster
                            if clusters:
                                top_cluster = clusters[0]  # Already sorted by serious_pct
                                age_str = f"{top_cluster['mean_age']:.0f}" if top_cluster['mean_age'] is not None else "N/A"
                                st.caption(
                                    f"💡 **Highest-risk cluster:** Cluster {top_cluster['cluster_id']} "
                                    f"({top_cluster['size']} cases, {top_cluster['serious_pct']:.1f}% serious, "
                                    f"mean age {age_str} years)"
                                )
                        else:
                            st.info("ℹ️ Not enough cases for clustering (minimum 20 cases with age data required).")
                        
                        # Explainable Quantum AI for Clustering
                        if clusters:
                            with st.expander("🔬 Explain Quantum Clustering", expanded=False):
                                clustering_explanation = explain_quantum_clustering(clusters, drug, reaction)
                                st.markdown(clustering_explanation['explanation'])
                                
                                with st.expander("📋 Regulatory Summary", expanded=False):
                                    st.code(clustering_explanation['regulatory_summary'], language=None)
                        
                        # Explainable Quantum AI for Clustering
                        if clusters:
                            with st.expander("🔬 Explain Quantum Clustering", expanded=False):
                                clustering_explanation = explain_quantum_clustering(clusters, drug, reaction)
                                st.markdown(clustering_explanation['explanation'])
                                
                                with st.expander("📋 Regulatory Summary", expanded=False):
                                    st.code(clustering_explanation['regulatory_summary'], language=None)

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

        # New Signals Detection (All Signals)
        st.markdown("---")
        st.subheader("🆕 New/Unexpected Signals")
        st.caption("Detects novel or unexpected drug-reaction signals across the dataset")
        
        if st.button("🔍 Detect New Signals", key="detect_new_signals", use_container_width=True):
            with st.spinner("Analyzing all drug-reaction pairs for unexpectedness..."):
                new_signals_df = detect_new_signals(
                    normalized_df,
                    min_cases=3,
                    unexpectedness_threshold=60.0,
                    top_n=20
                )
                
                if not new_signals_df.empty:
                    st.success(f"✅ Found {len(new_signals_df)} new/unexpected signal(s)")
                    
                    # Display table
                    display_df = new_signals_df[["drug", "reaction", "n_cases", "unexpectedness_score", "is_novel", "is_rare", "explanation"]].copy()
                    display_df.columns = ["Drug", "Reaction", "Cases", "Unexpectedness", "Novel", "Rare", "Explanation"]
                    display_df["Unexpectedness"] = display_df["Unexpectedness"].round(1)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Download button
                    csv = new_signals_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download New Signals (CSV)",
                        csv,
                        "new_signals.csv",
                        "text/csv"
                    )
                else:
                    st.info("ℹ️ No new/unexpected signals detected above threshold")
        
        # Class Effects Detection (All Classes)
        st.markdown("---")
        st.subheader("💊 Drug Class Effects")
        st.caption("Identifies reactions common across drug classes")
        
        if st.button("🔍 Detect Class Effects", key="detect_class_effects", use_container_width=True):
            with st.spinner("Analyzing drug classes for common reactions..."):
                class_effects = detect_class_effects(
                    normalized_df,
                    min_drugs_in_class=2,
                    min_cases_per_drug=3
                )
                
                if class_effects:
                    st.success(f"✅ Found {len(class_effects)} class effect(s)")
                    
                    class_effects_data = []
                    for effect in class_effects:
                        class_effects_data.append({
                            "Drug Class": effect["drug_class"],
                            "Reaction": effect["reaction"],
                            "Drugs Showing": effect["n_drugs_showing"],
                            "Total Cases": effect["total_cases"],
                            "Class PRR": f"{effect.get('class_prr', 0):.2f}" if effect.get('class_prr') else "N/A",
                        })
                    
                    class_effects_df = pd.DataFrame(class_effects_data)
                    st.dataframe(class_effects_df, use_container_width=True, hide_index=True)
                    
                    # Show details for top class effect
                    if class_effects:
                        top_effect = class_effects[0]
                        with st.expander(f"📋 Details: {top_effect['drug_class']} → {top_effect['reaction']}", expanded=False):
                            st.write(f"**Drugs in class showing this reaction:**")
                            for drug in top_effect["drugs_in_class"]:
                                st.write(f"- {drug}")
                else:
                    st.info("ℹ️ No significant class effects detected")
        
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
            
            # Explainable Quantum AI (XQI) - Show explanation for top signals
            with st.expander("🔬 Explainable Quantum AI (XQI)", expanded=False):
                st.caption("Transparent explanations for quantum-inspired ranking decisions")
                
                if ranked:
                    top_signal = ranked[0]
                    explanation = explain_quantum_ranking(top_signal, len(normalized_df))
                    
                    st.markdown("**Top Signal Explanation:**")
                    st.markdown(f"**{top_signal.get('drug', 'N/A')} → {top_signal.get('reaction', 'N/A')}**")
                    st.metric("Quantum Score", f"{explanation['quantum_score']:.3f}")
                    
                    # Component breakdown
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        comp = explanation['components']['rarity']
                        st.metric("Rarity", f"{comp['value']:.1%}", f"{comp['contribution']:.3f} pts")
                    with col2:
                        comp = explanation['components']['seriousness']
                        st.metric("Seriousness", f"{comp['value']:.1%}", f"{comp['contribution']:.3f} pts")
                    with col3:
                        comp = explanation['components']['recency']
                        st.metric("Recency", f"{comp['value']:.1%}", f"{comp['contribution']:.3f} pts")
                    with col4:
                        st.metric("Interactions", f"{explanation['interaction_score']:.3f}", "pts")
                    
                    # Natural language explanation
                    st.markdown("**Explanation:**")
                    st.markdown(explanation['explanation'])
                    
                    # Interaction details
                    if explanation['interactions']:
                        st.markdown("**Quantum Interactions Detected:**")
                        for interaction in explanation['interactions']:
                            st.write(f"- **{interaction['type']}**: {interaction['description']} (+{interaction['contribution']:.2f})")
                    
                    # Tunneling effects
                    if explanation['tunneling_effects']:
                        st.markdown("**Quantum Tunneling Effects:**")
                        for tunneling in explanation['tunneling_effects']:
                            st.write(f"- **{tunneling['type']}**: {tunneling['description']} (+{tunneling['contribution']:.2f})")
                    
                    # Regulatory summary
                    with st.expander("📋 Regulatory Summary (Audit Trail)", expanded=False):
                        st.code(explanation['regulatory_summary'], language=None)
                    
                    # Circuit diagram (conceptual)
                    circuit = generate_quantum_circuit_diagram(top_signal, len(normalized_df))
                    with st.expander("⚛️ Quantum Decision Path (Conceptual)", expanded=False):
                        st.caption("Simplified representation of quantum-inspired scoring decision path")
                        for step in circuit['circuit_steps']:
                            st.write(f"**Step {step['step']}: {step['gate']}**")
                            st.write(f"  Inputs: {', '.join(step['inputs'])}")
                            st.write(f"  Outputs: {', '.join(step['outputs'])}")
                            st.write("")
            
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
            
            # Add drill-down capability
            st.caption("💡 Select a drug-reaction pair to see detailed cases")
            selected_df = st.dataframe(
                q_df,
                use_container_width=True,
                hide_index=True,
                key="signals_table",
            )
            
            # Check for row selection (Streamlit 1.29+)
            if "signals_table.selection" in st.session_state:
                selection = st.session_state["signals_table.selection"]
                if selection and "rows" in selection and len(selection["rows"]) > 0:
                    selected_row_idx = selection["rows"][0]
                    if selected_row_idx < len(q_df):
                        selected_row = q_df.iloc[selected_row_idx]
                        selected_drug = selected_row["Drug"]
                        # Extract reaction from display (remove MedDRA PT)
                        selected_reaction_display = selected_row["Reaction"]
                        selected_reaction = selected_reaction_display.split(" (MedDRA")[0].strip()
                        
                        render_drug_reaction_drill_down(
                            selected_drug,
                            selected_reaction,
                            filtered_df,
                        )
            
            # Fallback: Use selectbox for compatibility
            st.markdown("---")
            with st.expander("🔍 Drill down to specific drug-reaction cases", expanded=False):
                if len(q_df) > 0:
                    signal_options = [
                        f"{row['Drug']} + {row['Reaction'].split(' (MedDRA')[0]} ({row['Count']} cases)"
                        for _, row in q_df.iterrows()
                    ]
                    selected_signal_idx = st.selectbox(
                        "Select drug-reaction pair",
                        range(len(q_df)),
                        format_func=lambda x: signal_options[x] if x < len(signal_options) else "",
                        key="signals_select",
                    )
                    
                    if selected_signal_idx is not None and selected_signal_idx < len(q_df):
                        selected_row = q_df.iloc[selected_signal_idx]
                        selected_drug = selected_row["Drug"]
                        selected_reaction_display = selected_row["Reaction"]
                        selected_reaction = selected_reaction_display.split(" (MedDRA")[0].strip()
                        
                        render_drug_reaction_drill_down(
                            selected_drug,
                            selected_reaction,
                            filtered_df,
                        )

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
        # Longitudinal Spike Detection
        if len(trend_df) >= 4:
            st.markdown("---")
            st.subheader("📈 Longitudinal Spike Detection")
            st.caption("Detects sudden increases in case counts over time")
            
            spike_method = st.radio(
                "Detection Method",
                ["Rolling Window", "Statistical Test (Poisson)", "Statistical Test (Normal)"],
                horizontal=True,
                key="spike_method"
            )
            
            if spike_method == "Rolling Window":
                spikes = detect_spikes(trend_data, window_size=3, threshold_multiplier=2.0, min_cases=5)
                if spikes:
                    st.success(f"🔍 Detected {len(spikes)} spike(s)")
                    spike_df = pd.DataFrame(spikes)
                    spike_df = spike_df[["period_str", "count", "baseline_mean", "z_score", "spike_ratio", "excess_cases"]]
                    spike_df.columns = ["Period", "Cases", "Baseline", "Z-Score", "Spike Ratio", "Excess Cases"]
                    st.dataframe(spike_df, use_container_width=True, hide_index=True)
                    
                    # Highlight spikes on chart
                    spike_periods = [s["period"] for s in spikes]
                    spike_counts = [s["count"] for s in spikes]
                    fig.add_scatter(
                        x=spike_periods,
                        y=spike_counts,
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='triangle-up'),
                        name='Spikes',
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ No significant spikes detected")
            
            elif "Poisson" in spike_method:
                spikes = detect_statistical_spikes(trend_data, method="poisson", alpha=0.05)
                if spikes:
                    st.success(f"🔍 Detected {len(spikes)} statistically significant spike(s)")
                    spike_df = pd.DataFrame(spikes)
                    spike_df = spike_df[["period_str", "count", "expected", "p_value"]]
                    spike_df.columns = ["Period", "Cases", "Expected", "P-Value"]
                    st.dataframe(spike_df, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ No statistically significant spikes detected")
            
            else:  # Normal
                spikes = detect_statistical_spikes(trend_data, method="normal", alpha=0.05)
                if spikes:
                    st.success(f"🔍 Detected {len(spikes)} statistically significant spike(s)")
                    spike_df = pd.DataFrame(spikes)
                    spike_df = spike_df[["period_str", "count", "expected", "z_score", "p_value"]]
                    spike_df.columns = ["Period", "Cases", "Expected", "Z-Score", "P-Value"]
                    st.dataframe(spike_df, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ No statistically significant spikes detected")
            
            # Changepoint Detection
            if len(trend_df) >= 6:
                with st.expander("🔄 Trend Changepoint Analysis", expanded=False):
                    changepoint = analyze_trend_changepoint(trend_data)
                    if changepoint:
                        st.warning(f"⚠️ Potential changepoint detected at {changepoint['split_period_str']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Before Mean", f"{changepoint['before_mean']:.1f}")
                        with col2:
                            st.metric("After Mean", f"{changepoint['after_mean']:.1f}")
                        st.metric("Change Ratio", f"{changepoint['change_ratio']:.2f}x")
                    else:
                        st.info("ℹ️ No significant changepoint detected")
        
        # Optional custom time-window comparison
        if len(trend_df) >= 3:
            with st.expander("Custom time-window comparison (exploratory)", expanded=False):
                period_series = trend_df["Period"]
                labels = period_series.dt.strftime("%b %Y").tolist()
                index_by_label = {label: idx for idx, label in enumerate(labels)}

                col_a, col_b = st.columns(2)
                max_window = min(12, len(trend_df))
                with col_a:
                    end_label_a = st.selectbox(
                        "Window A: end period",
                        labels,
                        index=len(labels) - 1,
                        key="trend_win_a_end",
                    )
                    size_a = st.slider(
                        "Window A: size (periods)",
                        min_value=1,
                        max_value=max_window,
                        value=min(3, max_window),
                        key="trend_win_a_size",
                    )
                with col_b:
                    end_label_b = st.selectbox(
                        "Window B: end period",
                        labels,
                        index=max(0, len(labels) - 1 - size_a),
                        key="trend_win_b_end",
                    )
                    size_b = st.slider(
                        "Window B: size (periods)",
                        min_value=1,
                        max_value=max_window,
                        value=min(3, max_window),
                        key="trend_win_b_size",
                    )

                try:
                    end_idx_a = index_by_label[end_label_a]
                    start_idx_a = max(0, end_idx_a - size_a + 1)
                    window_a = trend_df.iloc[start_idx_a : end_idx_a + 1]

                    end_idx_b = index_by_label[end_label_b]
                    start_idx_b = max(0, end_idx_b - size_b + 1)
                    window_b = trend_df.iloc[start_idx_b : end_idx_b + 1]

                    sum_a = int(window_a["Count"].sum())
                    sum_b = int(window_b["Count"].sum())
                    delta_ab = sum_a - sum_b
                    pct_ab = safe_divide(delta_ab, sum_b, 0) * 100 if sum_b else 0.0

                    range_a = f"{window_a['Period'].iloc[0].strftime('%b %Y')} \u2192 {window_a['Period'].iloc[-1].strftime('%b %Y')}"
                    range_b = f"{window_b['Period'].iloc[0].strftime('%b %Y')} \u2192 {window_b['Period'].iloc[-1].strftime('%b %Y')}"

                    st.metric(
                        "Window A vs Window B",
                        f"{sum_a:,} vs {sum_b:,}",
                        f"{delta_ab:+} ({pct_ab:.1f}%)",
                    )
                    st.caption(
                        f"Window A: {range_a} | Window B: {range_b}. "
                        "Use this to compare pre/post periods (e.g., launch, label change)."
                    )
                except Exception:
                    st.info("Unable to compute custom windows for the selected configuration.")

        # Quantum-inspired anomaly detection on the same trend
        if len(trend_df) >= 5:
            scored = quantum_anomaly.score_time_series(trend_df)
            anomalies = quantum_anomaly.detect_time_anomalies(trend_df)
            with st.expander("Quantum-inspired anomaly detection (experimental)", expanded=False):
                if anomalies.empty:
                    st.caption(
                        "No strong anomalies detected in the current time window using the heuristic quantum-inspired score."
                    )
                else:
                    # Show top anomalies
                    top = anomalies.head(10).copy()
                    top["Period"] = top["Period"].dt.strftime("%b %Y")
                    st.caption(
                        "Highlighted periods where case counts are unusually high or rapidly changing, "
                        "based on a combined z-score and curvature heuristic. Exploratory use only."
                    )
                    st.dataframe(
                        top[["Period", "Count", "z_score", "anomaly_score"]],
                        use_container_width=True,
                        hide_index=True,
                    )
        st.markdown("</div>", unsafe_allow_html=True)

    # Time-to-onset analysis
    if "onset_date" in filtered_df.columns and "start_date" in filtered_df.columns:
        _render_time_to_onset_analysis(filtered_df, filters)
    elif "onset_date" in filtered_df.columns:
        st.info("💡 Time-to-onset analysis requires both 'onset_date' and 'start_date' columns. Only 'onset_date' is available.")
    
    # Case series viewer
    _render_case_series_section(filtered_df, filters)

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
    
    if not summary.get("time_trend") and not top_co_reactions:
        st.info("Time trend and co-reaction data not available for this query.")


def _render_time_to_onset_analysis(filtered_df: pd.DataFrame, filters: Dict) -> None:
    """Render time-to-onset distribution and Weibull analysis."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("⏱️ Time-to-Onset Analysis")
    
    # Calculate TTO
    tto_df = calculate_time_to_onset(filtered_df)
    
    # Filter for specific drug-reaction if provided
    drug_filter = filters.get("drug")
    reaction_filter = filters.get("reaction")
    
    drug = drug_filter[0] if isinstance(drug_filter, list) and drug_filter else (drug_filter if isinstance(drug_filter, str) else None)
    reaction = reaction_filter[0] if isinstance(reaction_filter, list) and reaction_filter else (reaction_filter if isinstance(reaction_filter, str) else None)
    
    # Get TTO data
    tto_data = tto_df["tto_days"].dropna()
    tto_data = tto_data[tto_data >= 0]
    
    if len(tto_data) == 0:
        st.info("No valid time-to-onset data available. Requires both 'start_date' and 'onset_date' columns.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Basic statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cases with TTO", len(tto_data))
    with col2:
        st.metric("Mean TTO", f"{tto_data.mean():.1f} days")
    with col3:
        st.metric("Median TTO", f"{tto_data.median():.1f} days")
    with col4:
        st.metric("Range", f"{tto_data.min():.0f} - {tto_data.max():.0f} days")
    
    # Distribution histogram
    st.markdown("#### Distribution")
    fig = px.histogram(
        tto_df[tto_df["tto_days"] >= 0],
        x="tto_days",
        nbins=30,
        labels={"tto_days": "Time-to-Onset (days)", "count": "Number of Cases"},
        color_discrete_sequence=["#2563eb"],
    )
    fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    
    # Weibull analysis
    if len(tto_data) >= 3:
        st.markdown("#### Weibull Distribution Fit")
        weibull_params = fit_weibull(tto_data)
        
        if weibull_params.get("fit_success"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Shape Parameter (β)", f"{weibull_params['shape']:.3f}")
            with col2:
                st.metric("Scale Parameter (λ)", f"{weibull_params['scale']:.1f}")
            with col3:
                st.metric("Mean TTO (Weibull)", f"{weibull_params['mean']:.1f} days")
            
            st.caption(
                f"Goodness of fit: KS statistic = {weibull_params.get('ks_statistic', 0):.3f}, "
                f"p-value = {weibull_params.get('ks_pvalue', 0):.3f}. "
                "Shape < 1 indicates decreasing hazard (early events), > 1 indicates increasing hazard (late events)."
            )
        else:
            st.warning("Weibull fit failed. Insufficient data or fit error.")
    
    # Drug-reaction specific analysis (if filters applied)
    if drug and reaction:
        st.markdown("#### Drug-Reaction Specific Analysis")
        dr_analysis = analyze_drug_reaction_tto(tto_df, drug, reaction)
        
        if dr_analysis["n_with_tto"] > 0:
            st.write(f"**Cases:** {dr_analysis['n_cases']} | **With TTO:** {dr_analysis['n_with_tto']}")
            st.write(f"**Mean:** {dr_analysis['mean_tto']:.1f} days | **Median:** {dr_analysis['median_tto']:.1f} days")
            
            if dr_analysis.get("weibull") and dr_analysis["weibull"].get("fit_success"):
                st.write(f"**Weibull Shape:** {dr_analysis['weibull']['shape']:.3f} | **Scale:** {dr_analysis['weibull']['scale']:.1f}")
        else:
            st.info(f"No TTO data available for {drug} + {reaction}")
    
    st.markdown("</div>", unsafe_allow_html=True)


def _render_case_series_section(filtered_df: pd.DataFrame, filters: Dict) -> None:
    """Render case series viewer section."""
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    drug_filter = filters.get("drug")
    reaction_filter = filters.get("reaction")
    
    drug = drug_filter[0] if isinstance(drug_filter, list) and drug_filter else (drug_filter if isinstance(drug_filter, str) else None)
    reaction = reaction_filter[0] if isinstance(reaction_filter, list) and reaction_filter else (reaction_filter if isinstance(reaction_filter, str) else None)
    
    render_case_series_viewer(filtered_df, drug=drug, reaction=reaction, max_cases=50)
    
    st.markdown("</div>", unsafe_allow_html=True)


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
    export_col1, export_col2, export_col3 = st.columns(3)
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
    with export_col3:
        # E2B(R3) XML export
        try:
            e2b_xml = export_to_e2b(show_df, output_format="bytes")
            is_valid, validation_errors = validate_e2b_xml(e2b_xml.decode("utf-8"))
            
            if st.download_button(
                label="📋 Export as E2B(R3) XML",
                data=e2b_xml,
                file_name=f"aethersignal_e2b_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                mime="application/xml",
                use_container_width=True,
                help="ICH E2B(R3) format for regulatory submissions. Note: Validate against official DTD before regulatory use.",
            ):
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event("e2b_export", {"row_count": len(show_df), "valid": is_valid})
                
                if not is_valid and validation_errors:
                    st.warning(f"⚠️ E2B validation warnings: {', '.join(validation_errors[:3])}")
                elif is_valid:
                    st.success("✅ E2B XML generated successfully")
        except Exception as e:
            st.error(f"❌ E2B export failed: {str(e)}")
            st.info("E2B export requires proper case data structure. Ensure columns: caseid/primaryid, drug_name, reaction, age, sex, country, seriousness, outcome, dates.")
    
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
                from src.audit_trail import log_audit_event
                log_audit_event(
                    event="pdf_generated",
                    details={
                        "query": query_text[:100] if query_text else "",
                        "filters": {k: str(v)[:50] for k, v in filters.items()},
                        "source": source,
                        "matching_cases": summary["matching_cases"],
                    }
                )
            except Exception:
                pass  # Silently fail
    
    st.markdown("</div>", unsafe_allow_html=True)

