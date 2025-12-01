"""
Trend Alerts Panel for AetherSignal Results Display.
CHUNK 6.11-C: Option E - Full Tab for Deep Analysis
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

def render_trend_alerts_tab(normalized_df: pd.DataFrame):
    """
    Render comprehensive Trend Alerts tab (CHUNK 6.11-C: Option E).
    
    Shows:
    - Full trend alerts analysis
    - Light preview (fast)
    - Heavy analysis on demand
    - LLM interpretations
    - Actionable insights
    """
    if normalized_df is None or len(normalized_df) == 0:
        st.info("⚠️ No data available. Please load your dataset first.")
        return
    
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("⚠️ Trend Alerts - Comprehensive Analysis")
    st.caption("Automatic detection of trends, spikes, anomalies, and emerging safety signals")
    
    # Mode selector (Light vs Heavy)
    col1, col2 = st.columns([3, 1])
    with col1:
        analysis_mode = st.radio(
            "Analysis Mode",
            ["⚡ Light (Fast Preview)", "📊 Heavy (Full Analysis)"],
            horizontal=True,
            key="trend_alerts_mode",
            help="Light mode provides quick alerts. Heavy mode includes full statistical analysis and LLM interpretation."
        )
    
    with col2:
        # Use two rows for buttons to avoid overcrowding
        row1_cols = st.columns(5)
        row2_cols = st.columns(5)
        
        with row1_cols[0]:
            if st.button("🔄 Refresh", use_container_width=True):
                # Clear cache to force refresh
                if "trend_alerts_cache" in st.session_state:
                    del st.session_state.trend_alerts_cache
                st.rerun()
        with row1_cols[1]:
            # CHUNK 6.13: SAR Generation Button
            if st.button("📄 SAR", use_container_width=True, help="Generate Safety Assessment Report"):
                st.session_state["generate_sar"] = True
                st.rerun()
        with row1_cols[2]:
            # CHUNK 6.14: DSUR Generation Button
            if st.button("📘 DSUR", use_container_width=True, help="Generate Development Safety Update Report"):
                st.session_state["generate_dsur"] = True
                st.rerun()
        with row1_cols[3]:
            # CHUNK 6.14: PBRER Generation Button
            if st.button("📙 PBRER", use_container_width=True, help="Generate Periodic Benefit-Risk Evaluation Report"):
                st.session_state["generate_pbrer"] = True
                st.rerun()
        with row1_cols[4]:
            # CHUNK 6.15: CAPA Generation Button
            if st.button("🛠️ CAPA", use_container_width=True, help="Generate Corrective and Preventive Actions"):
                st.session_state["generate_capa"] = True
                st.rerun()
        
        with row2_cols[0]:
            # CHUNK 6.16: Inspection Readiness Button
            if st.button("📑 Inspection", use_container_width=True, help="Generate Inspection Readiness Package"):
                st.session_state["generate_inspection"] = True
                st.rerun()
        with row2_cols[1]:
            # CHUNK 6.18: CSP Generation Button
            if st.button("🧬 CSP", use_container_width=True, help="Generate Core Safety Profile"):
                st.session_state["generate_csp"] = True
                st.rerun()
        with row2_cols[2]:
            # CHUNK 6.19: Label Impact Assessment Button
            if st.button("📄 Label Impact", use_container_width=True, help="Generate Label Impact Assessment"):
                st.session_state["generate_label_impact"] = True
                st.rerun()
    
    # Determine mode
    use_heavy = "Heavy" in analysis_mode
    
    # Show loading indicator
    if use_heavy:
        with st.spinner("Running comprehensive trend analysis with LLM interpretation... This may take 30-60 seconds."):
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
    else:
        alerts_result = _get_trend_alerts(normalized_df, mode="light")
    
    # CHUNK 6.13/6.14: Check if report generation was requested (after alerts are loaded)
    if st.session_state.get("generate_sar", False):
        st.session_state["generate_sar"] = False
        if alerts_result:
            _generate_sar_report(normalized_df, alerts_result)
        else:
            # Force heavy mode for SAR if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_sar_report(normalized_df, alerts_result)
    
    # CHUNK 6.14: Check if DSUR generation was requested
    if st.session_state.get("generate_dsur", False):
        st.session_state["generate_dsur"] = False
        if alerts_result:
            _generate_dsur_report(normalized_df, alerts_result)
        else:
            # Force heavy mode for DSUR if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_dsur_report(normalized_df, alerts_result)
    
    # CHUNK 6.14: Check if PBRER generation was requested
    if st.session_state.get("generate_pbrer", False):
        st.session_state["generate_pbrer"] = False
        if alerts_result:
            _generate_pbrer_report(normalized_df, alerts_result)
        else:
            # Force heavy mode for PBRER if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_pbrer_report(normalized_df, alerts_result)
    
    # CHUNK 6.15: Check if CAPA generation was requested
    if st.session_state.get("generate_capa", False):
        st.session_state["generate_capa"] = False
        if alerts_result:
            _generate_capa_recommendations(normalized_df, alerts_result)
        else:
            # Force heavy mode for CAPA if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_capa_recommendations(normalized_df, alerts_result)
    
    # CHUNK 6.16: Check if Inspection Readiness generation was requested
    if st.session_state.get("generate_inspection", False):
        st.session_state["generate_inspection"] = False
        if alerts_result:
            _generate_inspection_readiness(normalized_df, alerts_result)
        else:
            # Force heavy mode for Inspection if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_inspection_readiness(normalized_df, alerts_result)
    
    # CHUNK 6.18: Check if CSP generation was requested
    if st.session_state.get("generate_csp", False):
        st.session_state["generate_csp"] = False
        if alerts_result:
            _generate_csp(normalized_df, alerts_result)
        else:
            # Force heavy mode for CSP if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_csp(normalized_df, alerts_result)
    
    # CHUNK 6.19: Check if Label Impact Assessment generation was requested
    if st.session_state.get("generate_label_impact", False):
        st.session_state["generate_label_impact"] = False
        if alerts_result:
            _generate_label_impact(normalized_df, alerts_result)
        else:
            # Force heavy mode for Label Impact if no alerts yet
            alerts_result = _get_trend_alerts(normalized_df, mode="heavy")
            if alerts_result:
                _generate_label_impact(normalized_df, alerts_result)
    
    if not alerts_result:
        st.info("ℹ️ No trend alerts detected in the current dataset.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Extract results
    alerts = alerts_result.get("alerts", [])
    spikes = alerts_result.get("spikes", [])
    emerging_signals = alerts_result.get("emerging_signals", [])
    trend_notes = alerts_result.get("trend_notes", [])
    rpf_ranked = alerts_result.get("rpf_ranked", [])  # CHUNK 6.12: Risk Prioritization Framework
    meta = alerts_result.get("meta", {})
    
    total_alerts = len(alerts)
    total_spikes = len(spikes)
    total_signals = len(emerging_signals)
    total_notes = len(trend_notes)
    
    # Summary metrics
    st.markdown("### 📊 Alert Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("High-Priority Alerts", total_alerts)
    with col2:
        st.metric("Detected Spikes", total_spikes)
    with col3:
        st.metric("Emerging Signals", total_signals)
    with col4:
        st.metric("Trend Notes", total_notes)
    
    # Show mode indicator
    mode_icon = "📊" if use_heavy else "⚡"
    mode_text = "Heavy Analysis (Full + LLM)" if use_heavy else "Light Analysis (Fast Preview)"
    st.caption(f"{mode_icon} {mode_text} | Total Cases: {meta.get('total_cases', 0):,}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # HIGH-PRIORITY ALERTS
    # ============================================================
    if alerts:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("🔴 High-Priority Alerts")
        st.caption(f"{len(alerts)} alerts requiring attention")
        
        for idx, alert in enumerate(alerts, 1):
            severity = alert.get("severity", "medium")
            message = alert.get("message", "")
            alert_type = alert.get("type", "")
            
            # Severity-based styling
            if severity == "high":
                st.error(f"**{idx}. {message}**")
            elif severity == "medium":
                st.warning(f"**{idx}. {message}**")
            else:
                st.info(f"**{idx}. {message}**")
            
            # CHUNK 6.11.5: Show structured LLM interpretation if available
            if alert.get("llm_explanation"):
                interpretation = alert.get("llm_explanation", {})
                with st.expander(f"🔍 Clinical Interpretation", expanded=False):
                    # Single sentence summary
                    if interpretation.get("single_sentence_summary"):
                        st.markdown(f"**Summary:** {interpretation['single_sentence_summary']}")
                        st.markdown("---")
                    
                    # Clinical relevance
                    if interpretation.get("clinical_relevance"):
                        st.markdown(f"**Clinical Relevance:**")
                        st.markdown(interpretation["clinical_relevance"])
                        st.markdown("---")
                    
                    # Possible causes
                    if interpretation.get("possible_causes"):
                        st.markdown("**Possible Causes:**")
                        for cause in interpretation["possible_causes"]:
                            st.markdown(f"- {cause}")
                        st.markdown("---")
                    
                    # Case characteristics
                    if interpretation.get("case_characteristics"):
                        st.markdown("**Case Characteristics:**")
                        st.markdown(interpretation["case_characteristics"])
                        st.markdown("---")
                    
                    # Regulatory context
                    if interpretation.get("regulatory_context"):
                        st.markdown("**Regulatory Context:**")
                        st.markdown(interpretation["regulatory_context"])
                        st.markdown("---")
                    
                    # Follow-up recommendations
                    if interpretation.get("recommended_followups"):
                        st.markdown("**Recommended Follow-ups:**")
                        for followup in interpretation["recommended_followups"]:
                            st.markdown(f"- {followup}")
            
            # Fallback: Show old-style interpretation if present (backwards compatibility)
            elif alert.get("has_llm_interpretation"):
                interpretation = alert.get("llm_interpretation", "")
                if interpretation:
                    with st.expander(f"💡 Clinical Interpretation", expanded=False):
                        st.markdown(interpretation)
            
            # CHUNK 6.11.7: Show time-series analysis if available
            if alert.get("time_series"):
                ts = alert.get("time_series", {})
                with st.expander(f"📊 Time-Series Analysis", expanded=False):
                    # Time-series chart
                    if ts.get("raw") and ts.get("ma") and ts.get("ewma"):
                        try:
                            # Prepare data for chart
                            chart_data = pd.DataFrame({
                                "Observed": ts["raw"],
                                "MA (3m)": ts["ma"],
                                "EWMA": ts["ewma"]
                            })
                            st.line_chart(chart_data)
                        except Exception:
                            pass
                    
                    # Statistical summary
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Latest Value", int(ts.get("latest_value", 0)) if ts.get("latest_value") else 0)
                        st.metric("Expected (MA)", f"{ts.get('expected_value', 0):.2f}" if ts.get("expected_value") else "N/A")
                    
                    with col2:
                        delta_val = ts.get("delta", 0)
                        delta_display = f"{delta_val:+.2f}" if delta_val else "0"
                        st.metric("Δ (Observed - Expected)", delta_display)
                        significance = ts.get("significance", 0)
                        sig_label = f"{significance:.2f}σ" if significance else "0"
                        st.metric("Significance Score", sig_label)
                    
                    # Control limits
                    if ts.get("limits"):
                        limits = ts["limits"]
                        st.markdown("**Control Limits (3σ):**")
                        st.markdown(f"- Upper Control Limit (UCL): {limits.get('ucl', 0):.2f}")
                        st.markdown(f"- Mean: {limits.get('mean', 0):.2f}")
                        st.markdown(f"- Lower Control Limit (LCL): {limits.get('lcl', 0):.2f}")
                    
                    # Anomalies
                    if ts.get("anomalies") and len(ts["anomalies"]) > 0:
                        st.warning(f"⚠️ Detected {len(ts['anomalies'])} anomaly/anomalies at indices: {ts['anomalies']}")
                    
                    # Change points
                    if ts.get("changepoints") and len(ts["changepoints"]) > 0:
                        periods = ts.get("periods", [])
                        changepoint_periods = [periods[idx] for idx in ts["changepoints"] if idx < len(periods)]
                        if changepoint_periods:
                            st.error(f"🔴 Detected {len(ts['changepoints'])} structural change-point(s) at: {', '.join(changepoint_periods[:5])}")
            
            # CHUNK 6.11.8 + 6.11.11: Show enhanced population subgroup analysis if available
            if alert.get("subgroups"):
                with st.expander("🧬 Population Subgroup Analysis (Enhanced)", expanded=False):
                    subgroups = alert.get("subgroups", {})
                    
                    # Show subgroup distributions
                    for subgroup_name, subgroup_data in subgroups.items():
                        st.markdown(f"#### {subgroup_name.replace('_', ' ').title()}")
                        
                        distribution = subgroup_data.get("distribution", {})
                        top_group = subgroup_data.get("top_group", "N/A")
                        top_value = subgroup_data.get("top_value", 0)
                        top_percentage = subgroup_data.get("top_percentage", 0)
                        anomaly_score = subgroup_data.get("anomaly_score", 1.0)
                        
                        # Display distribution as bar chart data
                        if distribution:
                            dist_df = pd.DataFrame({
                                "Group": list(distribution.keys()),
                                "Cases": list(distribution.values())
                            }).sort_values("Cases", ascending=False)
                            
                            st.bar_chart(dist_df.set_index("Group"))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Top Group:** {top_group}")
                                st.markdown(f"**Cases:** {top_value} ({top_percentage:.1f}% of total)")
                            with col2:
                                st.markdown(f"**Anomaly Score:** {anomaly_score:.2f}")
                                if anomaly_score > 2.0:
                                    st.warning(f"⚠️ Potential anomaly detected")
                            
                            # CHUNK 6.11.11: Show statistical tests if available
                            stat_tests = subgroup_data.get("statistical_tests")
                            if stat_tests:
                                st.markdown("**Statistical Tests:**")
                                test_col1, test_col2 = st.columns(2)
                                with test_col1:
                                    if stat_tests.get("p_value_chi2") is not None:
                                        p_val = stat_tests["p_value_chi2"]
                                        st.metric("Chi-square p-value", f"{p_val:.4f}")
                                        if p_val < 0.05:
                                            st.success("✅ Statistically significant difference")
                                        else:
                                            st.info("ℹ️ Not statistically significant")
                                with test_col2:
                                    if stat_tests.get("p_value_fisher") is not None:
                                        p_val_fisher = stat_tests["p_value_fisher"]
                                        st.metric("Fisher Exact p-value", f"{p_val_fisher:.4f}")
                                        if stat_tests.get("odds_ratio_fisher"):
                                            st.caption(f"Odds Ratio: {stat_tests['odds_ratio_fisher']:.2f}")
                                
                                if stat_tests.get("relative_risk"):
                                    st.caption(f"Relative Risk: {stat_tests['relative_risk']:.2f}×")
                            
                            # CHUNK 6.11.11: Show subgroup-specific PRR/ROR if available
                            subgroup_prr_ror = subgroup_data.get("subgroup_prr_ror")
                            if subgroup_prr_ror:
                                st.markdown("**Subgroup-Specific Disproportionality:**")
                                prr_col1, prr_col2 = st.columns(2)
                                with prr_col1:
                                    prr = subgroup_prr_ror.get("prr")
                                    if prr:
                                        st.metric(
                                            "PRR (Subgroup)",
                                            f"{prr:.2f}",
                                            help="Proportional Reporting Ratio for this subgroup"
                                        )
                                        if subgroup_prr_ror.get("prr_ci_lower") and subgroup_prr_ror.get("prr_ci_upper"):
                                            st.caption(
                                                f"95% CI: {subgroup_prr_ror['prr_ci_lower']:.2f} - "
                                                f"{subgroup_prr_ror['prr_ci_upper']:.2f}"
                                            )
                                with prr_col2:
                                    ror = subgroup_prr_ror.get("ror")
                                    if ror:
                                        st.metric(
                                            "ROR (Subgroup)",
                                            f"{ror:.2f}",
                                            help="Reporting Odds Ratio for this subgroup"
                                        )
                                        if subgroup_prr_ror.get("ror_ci_lower") and subgroup_prr_ror.get("ror_ci_upper"):
                                            st.caption(
                                                f"95% CI: {subgroup_prr_ror['ror_ci_lower']:.2f} - "
                                                f"{subgroup_prr_ror['ror_ci_upper']:.2f}"
                                            )
                            
                            if anomaly_score > 2.0:
                                st.warning(
                                    f"⚠️ Potential anomaly detected: {top_group} drives {top_value} cases "
                                    f"(anomaly score: {anomaly_score:.2f})"
                                )
                        
                        st.markdown("---")
                    
                    # CHUNK 6.11.11: Show concomitant drug analysis if available
                    if alert.get("details") and alert["details"].get("concomitant_drugs"):
                        concomitants = alert["details"]["concomitant_drugs"]
                        st.markdown("### 💊 Concomitant Drug Analysis")
                        
                        top_conc = concomitants.get("top_concomitants", {})
                        if top_conc:
                            conc_df = pd.DataFrame({
                                "Concomitant Drug": list(top_conc.keys()),
                                "Cases": list(top_conc.values())
                            }).sort_values("Cases", ascending=False)
                            
                            st.bar_chart(conc_df.set_index("Concomitant Drug"))
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Concomitant Drugs", concomitants.get("total_concomitant_drugs", 0))
                            with col2:
                                st.metric(
                                    "Cases with Concomitants",
                                    concomitants.get("cases_with_concomitant", 0)
                                )
                            with col3:
                                conc_ratio = concomitants.get("concomitant_ratio", 0.0)
                                st.metric("Concomitant Ratio", f"{conc_ratio:.1%}")
                            
                            if conc_ratio > 0.3:  # More than 30% have concomitants
                                st.warning(
                                    "⚠️ High concomitant drug use detected. "
                                    "Review for potential drug-drug interactions."
                                )
                        
                        st.markdown("---")
                    
                    # Show epidemiological interpretation if available
                    if alert.get("subgroup_interpretation"):
                        interpretation = alert.get("subgroup_interpretation", {})
                        
                        st.markdown("### 📊 Epidemiological Interpretation")
                        
                        if interpretation.get("demographic_vulnerabilities"):
                            st.markdown(f"**Demographic Vulnerabilities:**")
                            st.markdown(interpretation["demographic_vulnerabilities"])
                            st.markdown("---")
                        
                        if interpretation.get("indication_specific_notes"):
                            st.markdown(f"**Indication-Specific Notes:**")
                            st.markdown(interpretation["indication_specific_notes"])
                            st.markdown("---")
                        
                        if interpretation.get("dose_related_findings"):
                            st.markdown(f"**Dose-Related Findings:**")
                            st.markdown(interpretation["dose_related_findings"])
                            st.markdown("---")
                        
                        if interpretation.get("key_findings"):
                            st.markdown("**Key Findings:**")
                            for finding in interpretation["key_findings"]:
                                st.markdown(f"- {finding}")
                            st.markdown("---")
                        
                        if interpretation.get("possible_risk_factors"):
                            st.markdown("**Possible Risk Factors:**")
                            for factor in interpretation["possible_risk_factors"]:
                                st.markdown(f"- {factor}")
                            st.markdown("---")
                        
                        if interpretation.get("recommendations"):
                            st.markdown("**Recommendations:**")
                            for rec in interpretation["recommendations"]:
                                st.markdown(f"- {rec}")
            
            # CHUNK 6.11.12: Show narrative clusters if available
            if alert.get("narrative_clusters"):
                with st.expander("🧠 Narrative Semantic Clusters", expanded=False):
                    clusters = alert.get("narrative_clusters", [])
                    
                    if not clusters:
                        st.info("No meaningful narrative clusters detected.")
                    else:
                        st.markdown(f"**Detected {len(clusters)} narrative pattern(s)**")
                        st.markdown("---")
                        
                        for c in clusters:
                            cluster_id = c.get("cluster_id", "N/A")
                            cluster_size = c.get("size", 0)
                            summary = c.get("summary", {})
                            
                            if summary:
                                cluster_label = summary.get("cluster_label", f"Cluster {cluster_id}")
                                one_sentence = summary.get("one_sentence_summary", "")
                                key_symptoms = summary.get("key_symptoms", [])
                                possible_mechanisms = summary.get("possible_mechanisms", [])
                                clinical_risk = summary.get("clinical_risk", "medium")
                                regulatory_relevance = summary.get("regulatory_relevance", "")
                            else:
                                cluster_label = f"Cluster {cluster_id}"
                                one_sentence = "Narrative cluster detected."
                                key_symptoms = []
                                possible_mechanisms = []
                                clinical_risk = "medium"
                                regulatory_relevance = ""
                            
                            st.subheader(f"Cluster {cluster_id} — {cluster_label}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Cluster Size", f"{cluster_size} cases")
                            with col2:
                                risk_colors = {
                                    "low": "🟢",
                                    "medium": "🟡",
                                    "high": "🟠",
                                    "critical": "🔴"
                                }
                                risk_icon = risk_colors.get(clinical_risk.lower(), "🟡")
                                st.metric("Clinical Risk", f"{risk_icon} {clinical_risk.title()}")
                            
                            if one_sentence:
                                st.markdown(f"**Summary:** {one_sentence}")
                            
                            if key_symptoms:
                                st.markdown("**Key Symptoms:**")
                                st.write(", ".join(key_symptoms))
                            
                            if possible_mechanisms:
                                st.markdown("**Possible Mechanisms:**")
                                for mechanism in possible_mechanisms:
                                    st.write(f"- {mechanism}")
                            
                            if regulatory_relevance:
                                st.markdown("**Regulatory Relevance:**")
                                st.write(regulatory_relevance)
                            
                            # Show example narratives
                            examples = c.get("examples", [])
                            if examples:
                                with st.expander(f"View Example Narratives ({len(examples)} shown)", expanded=False):
                                    for i, example in enumerate(examples[:5], 1):
                                        st.markdown(f"**Example {i}:**")
                                        st.text(example[:500] + ("..." if len(example) > 500 else ""))
                                        st.markdown("---")
                            
                            st.markdown("---")
            
            # CHUNK 6.11.13: Show lot/batch alerts if available
            if alert.get("lot_alerts"):
                with st.expander("🏭 Batch / Lot Spike Alerts", expanded=False):
                    lots = alert.get("lot_alerts", [])
                    
                    if not lots:
                        st.info("No batch-level spikes detected.")
                    else:
                        st.markdown(f"**Detected {len(lots)} batch anomaly/ies**")
                        st.markdown("---")
                        
                        for lot in lots:
                            lot_number = lot.get("lot_number", "N/A")
                            count = lot.get("count", 0)
                            spike_ratio = lot.get("spike_ratio", 0.0)
                            p_value = lot.get("p_value", 1.0)
                            drug = lot.get("drug", "N/A")
                            top_reactions = lot.get("top_reactions", [])
                            serious_count = lot.get("serious_count", 0)
                            serious_ratio = lot.get("serious_ratio", 0.0)
                            interpretation = lot.get("interpretation", {})
                            
                            st.subheader(f"Lot {lot_number} — {count} cases ({spike_ratio:.2f}× above average)")
                            
                            # Key metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Spike Ratio", f"{spike_ratio:.2f}×")
                            with col2:
                                st.metric("P-value", f"{p_value:.4f}")
                            with col3:
                                st.metric("Serious Cases", f"{serious_count} ({serious_ratio:.1%})")
                            
                            st.markdown(f"**Drug:** {drug}")
                            
                            if top_reactions:
                                st.markdown("**Top Reactions:**")
                                st.write(", ".join(top_reactions[:5]))
                            
                            # LLM Interpretation
                            if interpretation:
                                st.markdown("### 🔬 Clinical Interpretation")
                                
                                one_sentence = interpretation.get("one_sentence_summary", "")
                                if one_sentence:
                                    st.markdown(f"**Summary:** {one_sentence}")
                                
                                manufacturing_issues = interpretation.get("possible_manufacturing_issues", [])
                                if manufacturing_issues:
                                    st.markdown("**Possible Manufacturing Issues:**")
                                    for issue in manufacturing_issues:
                                        st.write(f"- {issue}")
                                
                                storage_issues = interpretation.get("possible_storage_issues", [])
                                if storage_issues:
                                    st.markdown("**Possible Storage Issues:**")
                                    for issue in storage_issues:
                                        st.write(f"- {issue}")
                                
                                contamination = interpretation.get("contamination_likelihood", "unknown")
                                if contamination:
                                    st.markdown(f"**Contamination Likelihood:** {contamination.title()}")
                                
                                regulatory_urgency = interpretation.get("regulatory_urgency", "unknown")
                                if regulatory_urgency:
                                    urgency_colors = {
                                        "low": "🟢",
                                        "medium": "🟡",
                                        "high": "🟠",
                                        "critical": "🔴"
                                    }
                                    urgency_icon = urgency_colors.get(regulatory_urgency.lower(), "🟡")
                                    st.markdown(f"**Regulatory Urgency:** {urgency_icon} {regulatory_urgency.title()}")
                                
                                next_steps = interpretation.get("recommended_next_steps", [])
                                if next_steps:
                                    st.markdown("**Recommended Next Steps:**")
                                    for step in next_steps:
                                        st.write(f"- {step}")
                            
                            st.markdown("---")
            
            # CHUNK 6.12: Risk Prioritization Framework - Show RPF section after lot alerts
            # (This will be added as a separate section after all alerts)
            
            # CHUNK 6.11.9: Show dose-response and cumulative risk analysis if available
            if alert.get("dose_response") or alert.get("cumulative_risk"):
                with st.expander("📈 Dose-Response & Exposure Modeling", expanded=False):
                    
                    # Dose-Response Analysis
                    if alert.get("dose_response"):
                        dr = alert.get("dose_response", {})
                        
                        st.markdown("### Dose-Response Analysis")
                        
                        # Dose counts bar chart
                        if dr.get("dose_counts"):
                            dose_counts = dr["dose_counts"]
                            dose_order = dr.get("dose_order", list(dose_counts.keys()))
                            
                            # Prepare data for chart (in dose order)
                            chart_data = {}
                            for dose_bucket in dose_order:
                                if dose_bucket in dose_counts:
                                    chart_data[dose_bucket] = dose_counts[dose_bucket]
                            
                            if chart_data:
                                dose_df = pd.DataFrame({
                                    "Dose Bucket": list(chart_data.keys()),
                                    "Cases": list(chart_data.values())
                                })
                                st.bar_chart(dose_df.set_index("Dose Bucket"))
                        
                        # Exposure-adjusted risk line chart
                        if dr.get("exposure_adjusted"):
                            exposure_adj = dr["exposure_adjusted"]
                            dose_order = dr.get("dose_order", list(exposure_adj.keys()))
                            
                            # Prepare data for chart
                            chart_data = {}
                            for dose_bucket in dose_order:
                                if dose_bucket in exposure_adj:
                                    chart_data[dose_bucket] = exposure_adj[dose_bucket]
                            
                            if chart_data:
                                exp_df = pd.DataFrame({
                                    "Dose Bucket": list(chart_data.keys()),
                                    "Exposure-Adjusted Rate": list(chart_data.values())
                                })
                                st.line_chart(exp_df.set_index("Dose Bucket"))
                        
                        # Summary metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            significance = dr.get("significance", 1.0)
                            st.metric("Significance Score", f"{significance:.2f}×")
                        with col2:
                            trend_dir = dr.get("trend_direction", "unknown")
                            st.metric("Trend Direction", trend_dir.title())
                        
                        # Dose range
                        if dr.get("dose_range"):
                            dose_range = dr["dose_range"]
                            st.caption(f"Dose Range: {dose_range.get('min', 0):.1f}mg - {dose_range.get('max', 0):.1f}mg")
                        
                        st.markdown("---")
                    
                    # Cumulative Risk Analysis
                    if alert.get("cumulative_risk"):
                        cr = alert.get("cumulative_risk", {})
                        
                        st.markdown("### Cumulative Risk Over Time")
                        
                        # Cumulative risk line chart
                        if cr.get("cumulative"):
                            cumulative = cr["cumulative"]
                            periods = cr.get("periods", list(cumulative.keys()))
                            
                            # Prepare data for chart
                            chart_data = {}
                            for period in periods:
                                if period in cumulative:
                                    chart_data[period] = cumulative[period]
                            
                            if chart_data:
                                cum_df = pd.DataFrame({
                                    "Period": list(chart_data.keys()),
                                    "Cumulative Cases": list(chart_data.values())
                                })
                                st.line_chart(cum_df.set_index("Period"))
                        
                        # Summary metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            total_cases = cr.get("total_cases", 0)
                            st.metric("Total Cases", total_cases)
                        with col2:
                            is_increasing = cr.get("is_increasing", False)
                            trend_icon = "📈" if is_increasing else "📉"
                            st.metric("Trend", f"{trend_icon} {'Increasing' if is_increasing else 'Stable/Decreasing'}")
                        
                        # Monthly breakdown if available
                        if cr.get("monthly"):
                            st.markdown("**Monthly Breakdown:**")
                            monthly = cr["monthly"]
                            periods = cr.get("periods", list(monthly.keys()))
                            monthly_data = {period: monthly.get(period, 0) for period in periods}
                            monthly_df = pd.DataFrame({
                                "Period": list(monthly_data.keys()),
                                "Monthly Cases": list(monthly_data.values())
                            })
                            st.dataframe(monthly_df, use_container_width=True, hide_index=True)
                        
                        st.markdown("---")
                    
                    # LLM Interpretation
                    if alert.get("dose_interpretation"):
                        interpretation = alert.get("dose_interpretation", {})
                        
                        st.markdown("### 🔬 Clinical Interpretation")
                        
                        if interpretation.get("clinical_implications"):
                            st.markdown(f"**Clinical Implications:**")
                            st.markdown(interpretation["clinical_implications"])
                            st.markdown("---")
                        
                        if interpretation.get("potential_mechanisms"):
                            st.markdown("**Potential Mechanisms:**")
                            for mechanism in interpretation["potential_mechanisms"]:
                                st.markdown(f"- {mechanism}")
                            st.markdown("---")
                        
                        if interpretation.get("risk_management"):
                            st.markdown("**Risk Management Recommendations:**")
                            for rec in interpretation["risk_management"]:
                                st.markdown(f"- {rec}")
            
            # CHUNK 6.11.10: Show risk dynamics analysis if available
            if alert.get("risk_dynamics"):
                with st.expander("📊 Risk Dynamics Analysis", expanded=False):
                    rd = alert.get("risk_dynamics", {})
                    
                    # Velocity & Acceleration Analysis
                    vel_acc = rd.get("velocity_acceleration")
                    if vel_acc:
                        st.markdown("### Velocity & Acceleration")
                        
                        velocity = vel_acc.get("velocity", [])
                        acceleration = vel_acc.get("acceleration", [])
                        
                        if velocity and acceleration:
                            # Prepare chart data
                            # Velocity has one less point than original, acceleration has two less
                            chart_data = {}
                            if len(velocity) > 0:
                                chart_data["Velocity"] = {f"Period_{i+1}": v for i, v in enumerate(velocity)}
                            if len(acceleration) > 0:
                                chart_data["Acceleration"] = {f"Period_{i+2}": a for i, a in enumerate(acceleration)}
                            
                            if chart_data:
                                # Combine into single DataFrame
                                max_len = max(len(v) for v in chart_data.values())
                                chart_df_data = {}
                                for key, values in chart_data.items():
                                    padded = list(values.values()) + [None] * (max_len - len(values))
                                    chart_df_data[key] = padded
                                
                                chart_df = pd.DataFrame(chart_df_data)
                                st.line_chart(chart_df)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            acc_score = vel_acc.get("acceleration_score", 0.0)
                            st.metric("Acceleration Score", f"{acc_score:.2f}")
                        with col2:
                            trend_class = vel_acc.get("trend_classification", "unknown")
                            st.metric("Trend Classification", trend_class.title())
                        with col3:
                            is_acc = vel_acc.get("is_accelerating", False)
                            trend_icon = "📈" if is_acc else "📉" if vel_acc.get("is_decelerating", False) else "➡️"
                            st.metric("Risk Status", f"{trend_icon} {'Accelerating' if is_acc else 'Stable/Decelerating'}")
                        
                        # Velocity details
                        if vel_acc.get("velocity_ratio"):
                            st.caption(f"Velocity Ratio (Recent/Baseline): {vel_acc['velocity_ratio']:.2f}×")
                        
                        st.markdown("---")
                    
                    # Incident Rate Slope
                    slope = rd.get("incident_rate_slope")
                    if slope:
                        st.markdown("### Incident Rate Slope")
                        col1, col2 = st.columns(2)
                        with col1:
                            slope_raw = slope.get("slope_raw", 0.0)
                            st.metric("Raw Rate Slope", f"{slope_raw:.3f}")
                        with col2:
                            direction = slope.get("direction", "unknown")
                            st.metric("Direction", direction.title())
                        
                        if slope.get("slope_exposure_adjusted") is not None:
                            st.caption(f"Exposure-Adjusted Slope: {slope['slope_exposure_adjusted']:.3f}")
                        
                        st.markdown("---")
                    
                    # Change-Point Detection
                    changepoints = rd.get("changepoints", [])
                    changepoints_context = rd.get("changepoints_with_context", [])
                    
                    if changepoints_context:
                        st.markdown("### Structural Change-Points Detected")
                        
                        for cp in changepoints_context:
                            st.markdown(f"**Period:** {cp.get('period', 'N/A')}")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Before Mean", f"{cp.get('before_mean', 0):.1f}")
                            with col2:
                                st.metric("After Mean", f"{cp.get('after_mean', 0):.1f}")
                            with col3:
                                ratio = cp.get("change_ratio", 1.0)
                                st.metric("Change Ratio", f"{ratio:.2f}×")
                            
                            st.markdown("---")
                    elif changepoints:
                        st.warning(f"⚠️ Detected {len(changepoints)} structural change-point(s) at indices: {changepoints}")
                    else:
                        st.info("ℹ️ No significant structural change-points detected.")
                    
                    # LLM Interpretation
                    if alert.get("risk_dynamics_interpretation"):
                        interpretation = alert.get("risk_dynamics_interpretation", {})
                        
                        st.markdown("### 🔬 Clinical Interpretation")
                        
                        if interpretation.get("clinical_implications"):
                            st.markdown(f"**Clinical Implications:**")
                            st.markdown(interpretation["clinical_implications"])
                            st.markdown("---")
                        
                        if interpretation.get("possible_explanations"):
                            st.markdown("**Possible Explanations:**")
                            for explanation in interpretation["possible_explanations"]:
                                st.markdown(f"- {explanation}")
                            st.markdown("---")
                        
                        if interpretation.get("risk_level"):
                            st.markdown(f"**Assessed Risk Level:** {interpretation['risk_level']}")
                            st.markdown("---")
                        
                        if interpretation.get("recommended_actions"):
                            st.markdown("**Recommended Actions:**")
                            for action in interpretation["recommended_actions"]:
                                st.markdown(f"- {action}")
            
            st.markdown("---")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # DETECTED SPIKES
    # ============================================================
    if spikes:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("📈 Detected Spikes")
        st.caption(f"{len(spikes)} temporal spikes detected")
        
        # Create spikes dataframe for display
        spike_data = []
        for spike in spikes:
            spike_data.append({
                "Type": spike.get("type", "").replace("_", " ").title(),
                "Entity": spike.get("drug") or spike.get("reaction") or spike.get("entity", "N/A"),
                "Period": spike.get("period", ""),
                "Cases": spike.get("count", 0),
                "Baseline": f"{spike.get('baseline', 0):.1f}",
                "Increase": f"{spike.get('increase_ratio', 1.0):.1f}x",
                "Severity": spike.get("severity", "medium").title()
            })
        
        spike_df = pd.DataFrame(spike_data)
        st.dataframe(spike_df, use_container_width=True, hide_index=True)
        
        # Expandable details
        for idx, spike in enumerate(spikes, 1):
            with st.expander(f"🔍 Spike {idx}: {spike.get('message', '')[:60]}...", expanded=False):
                st.json(spike)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # EMERGING SIGNALS
    # ============================================================
    if emerging_signals:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("🆕 Emerging Signals")
        st.caption(f"{len(emerging_signals)} potential new safety signals detected")
        
        for idx, signal in enumerate(emerging_signals, 1):
            signal_type = signal.get("type", "")
            drug = signal.get("drug", "")
            reaction = signal.get("reaction", "")
            message = signal.get("message", "")
            
            st.markdown(f"**{idx}. {drug} + {reaction}**")
            st.markdown(f"*{message}*")
            
            # Show signal details
            if signal.get("recent_cases"):
                st.metric("Recent Cases (last 3 months)", signal.get("recent_cases", 0))
            
            # Show LLM interpretation if available
            if signal.get("has_llm_interpretation"):
                interpretation = signal.get("llm_interpretation", "")
                if interpretation:
                    with st.expander(f"💡 Signal Assessment", expanded=False):
                        st.markdown(interpretation)
            
            st.markdown("---")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # TREND NOTES
    # ============================================================
    if trend_notes:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("📝 Trend Notes")
        st.caption(f"{len(trend_notes)} notable trends identified")
        
        for note in trend_notes:
            st.markdown(f"• {note}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # CHUNK 6.12: RISK PRIORITIZATION FRAMEWORK (RPF)
    # ============================================================
    if rpf_ranked:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.subheader("📊 Risk Prioritization Framework (RPF)")
        st.caption("FDA/EMA-aligned automated signal prioritization based on 5-pillar weighted scoring")
        
        # RPF Summary Metrics
        critical_count = sum(1 for r in rpf_ranked if "🔥 Critical" in r.get("risk_level", ""))
        high_count = sum(1 for r in rpf_ranked if "⚠️ High" in r.get("risk_level", ""))
        medium_count = sum(1 for r in rpf_ranked if "🟡 Medium" in r.get("risk_level", ""))
        low_count = sum(1 for r in rpf_ranked if "🟢 Low" in r.get("risk_level", ""))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔥 Critical", critical_count, help="Score ≥ 80")
        with col2:
            st.metric("⚠️ High", high_count, help="Score 60-79")
        with col3:
            st.metric("🟡 Medium", medium_count, help="Score 40-59")
        with col4:
            st.metric("🟢 Low", low_count, help="Score < 40")
        
        st.markdown("---")
        
        # Top 10 Ranked Signals
        with st.expander("📊 Ranked Signals (Top 10)", expanded=True):
            for idx, entry in enumerate(rpf_ranked[:10], 1):
                signal = entry.get("signal", {})
                rpf_score = entry.get("rpf_score", 0)
                risk_level = entry.get("risk_level", "Unknown")
                scores = entry.get("scores", {})
                
                drug = signal.get("drug", "Unknown Drug")
                reaction = signal.get("reaction", "Unknown Reaction")
                
                # Color code based on risk level
                if "🔥 Critical" in risk_level:
                    risk_color = "#DC2626"  # Red
                    border_color = "#EF4444"
                elif "⚠️ High" in risk_level:
                    risk_color = "#F59E0B"  # Orange
                    border_color = "#F97316"
                elif "🟡 Medium" in risk_level:
                    risk_color = "#EAB308"  # Yellow
                    border_color = "#FCD34D"
                else:
                    risk_color = "#10B981"  # Green
                    border_color = "#34D399"
                
                st.markdown(
                    f"""
                    <div style="
                        border-left: 4px solid {border_color};
                        padding: 12px 16px;
                        margin-bottom: 12px;
                        background: rgba(255, 255, 255, 0.8);
                        border-radius: 6px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 1.1em; color: {risk_color};">
                                    #{idx}. {risk_level}
                                </strong>
                                <p style="margin: 4px 0; font-size: 0.95em;">
                                    <strong>{drug}</strong> → <strong>{reaction}</strong>
                                </p>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.5em; font-weight: bold; color: {risk_color};">
                                    {rpf_score:.1f}
                                </div>
                                <div style="font-size: 0.8em; color: #6B7280;">RPF Score</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Sub-scores breakdown
                with st.expander(f"View Score Breakdown", expanded=False):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        disp_score = scores.get("disproportionality", 0)
                        st.metric("Disproportionality", f"{disp_score:.2f}", help="30% weight - ROR/PRR strength")
                    
                    with col2:
                        serious_score = scores.get("seriousness", 0)
                        st.metric("Seriousness", f"{serious_score:.2f}", help="25% weight - Serious/fatal cases")
                    
                    with col3:
                        coherence_score = scores.get("clinical_coherence", 0)
                        st.metric("Clinical Coherence", f"{coherence_score:.2f}", help="15% weight - Biological plausibility")
                    
                    with col4:
                        trend_score = scores.get("trend_strength", 0)
                        st.metric("Trend Strength", f"{trend_score:.2f}", help="20% weight - Temporal patterns")
                    
                    with col5:
                        lot_score = scores.get("lot_risk", 0)
                        st.metric("Lot Risk", f"{lot_score:.2f}", help="10% weight - Batch anomalies")
                    
                    # Additional signal details
                    st.markdown("**Signal Details:**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"Case Count: {signal.get('case_count', 0)}")
                        st.write(f"Serious Cases: {signal.get('serious_count', 0)}")
                    with col_b:
                        if signal.get("ror"):
                            st.write(f"ROR: {signal.get('ror', 0):.2f}")
                        if signal.get("prr"):
                            st.write(f"PRR: {signal.get('prr', 0):.2f}")
                
                if idx < min(10, len(rpf_ranked)):
                    st.markdown("---")
        
        st.markdown("</div>", unsafe_allow_html=True)
    elif use_heavy:
        # Show message if no RPF data in heavy mode
        st.info("💡 Risk Prioritization Framework (RPF) will appear here when signals are detected in Heavy mode.")
    
    # ============================================================
    # NO ALERTS MESSAGE
    # ============================================================
    if not alerts and not spikes and not emerging_signals and not trend_notes:
        st.success("✅ No significant trend alerts detected in the current dataset.")
        st.info("💡 This could mean:\n- Your dataset has stable reporting patterns\n- No unusual spikes or anomalies detected\n- Try switching to Heavy mode for deeper analysis")


def _get_trend_alerts(normalized_df: pd.DataFrame, mode: str = "light") -> Optional[Dict[str, Any]]:
    """
    Get trend alerts with caching support.
    
    Args:
        normalized_df: DataFrame with PV data
        mode: "light" or "heavy"
    
    Returns:
        Dictionary with alerts, spikes, signals, notes
    """
    try:
        from src.ai.trend_alerts import detect_trend_alerts, detect_trend_alerts_light, detect_trend_alerts_heavy
        
        # Check cache
        cache_key = f"trend_alerts_{mode}_{len(normalized_df)}"
        if cache_key in st.session_state.get("trend_alerts_cache", {}):
            return st.session_state.trend_alerts_cache[cache_key]
        
        # Run detection
        if mode == "light":
            result = detect_trend_alerts_light(normalized_df)
        else:
            result = detect_trend_alerts_heavy(normalized_df)
        
        # Cache result
        if "trend_alerts_cache" not in st.session_state:
            st.session_state.trend_alerts_cache = {}
        st.session_state.trend_alerts_cache[cache_key] = result
        
        return result
    except Exception as e:
        st.error(f"Error generating trend alerts: {str(e)}")
        return None


def _generate_sar_report(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Safety Assessment Report (SAR) from trend alerts (CHUNK 6.13).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.sar_generator import SARGenerator
        from datetime import datetime
        
        sar_gen = SARGenerator()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        rpf_ranked = alerts.get("rpf_ranked", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
            if alert.get("subgroups"):
                subgroups.update(alert.get("subgroups", {}))
            if alert.get("lot_alerts"):
                lot_findings.extend(alert.get("lot_alerts", []))
            if alert.get("narrative_clusters"):
                narrative_highlights.extend(alert.get("narrative_clusters", []))
        
        # Build metadata
        meta = {
            "drug": "Multiple Drugs",  # Can be extracted from filters if available
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df))
        }
        
        # Build payload
        payload = sar_gen.build_sar_payload(
            alerts=alerts,
            signals=signals,
            subgroups=subgroups if subgroups else None,
            lot_findings=lot_findings if lot_findings else None,
            narrative_highlights=narrative_highlights if narrative_highlights else None,
            meta=meta
        )
        
        # Generate SAR (heavy mode)
        with st.spinner("📄 Generating Safety Assessment Report... This may take 30-60 seconds."):
            sar_content = sar_gen.generate_sar(payload, heavy=True)
        
        if sar_content:
            # Store in session state
            st.session_state["sar_report"] = {
                "content": sar_content,
                "meta": meta,
                "generated_on": datetime.now().isoformat(),
                "payload": payload  # Store for reference
            }
            st.success("✅ SAR report generated successfully! View it in the 'SAR Report' tab.")
            st.info("💡 The SAR includes comprehensive analysis of trends, RPF rankings, subgroups, lot findings, and narrative highlights.")
        else:
            st.error("❌ Failed to generate SAR report. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating SAR: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_dsur_report(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Development Safety Update Report (DSUR) from trend alerts (CHUNK 6.14).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.dsur_pbrer_generator import DSURPBRERGenerator
        from datetime import datetime
        
        gen = DSURPBRERGenerator()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
            if alert.get("subgroups"):
                subgroups.update(alert.get("subgroups", {}))
            if alert.get("lot_alerts"):
                lot_findings.extend(alert.get("lot_alerts", []))
            if alert.get("narrative_clusters"):
                narrative_highlights.extend(alert.get("narrative_clusters", []))
        
        # Build metadata
        meta = {
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df)),
            "period": "Annual"
        }
        
        # Build payload
        payload = gen.build_payload(
            alerts=alerts,
            signals=signals,
            subgroups=subgroups if subgroups else None,
            lot_findings=lot_findings if lot_findings else None,
            narrative_highlights=narrative_highlights if narrative_highlights else None,
            meta=meta
        )
        
        # Generate DSUR (heavy mode)
        with st.spinner("📘 Generating Development Safety Update Report (DSUR)... This may take 30-60 seconds."):
            dsur_content = gen.generate_dsur(payload, heavy=True)
        
        if dsur_content:
            # Store in session state
            st.session_state["dsur_report"] = {
                "content": dsur_content,
                "meta": meta,
                "generated_on": datetime.now().isoformat(),
                "payload": payload
            }
            st.success("✅ DSUR report generated successfully! View it in the 'DSUR / PBRER' tab.")
            st.info("💡 The DSUR includes comprehensive analysis according to ICH E2F guidelines.")
        else:
            st.error("❌ Failed to generate DSUR report. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating DSUR: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_pbrer_report(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Periodic Benefit-Risk Evaluation Report (PBRER) from trend alerts (CHUNK 6.14).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.dsur_pbrer_generator import DSURPBRERGenerator
        from datetime import datetime
        
        gen = DSURPBRERGenerator()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
            if alert.get("subgroups"):
                subgroups.update(alert.get("subgroups", {}))
            if alert.get("lot_alerts"):
                lot_findings.extend(alert.get("lot_alerts", []))
            if alert.get("narrative_clusters"):
                narrative_highlights.extend(alert.get("narrative_clusters", []))
        
        # Build metadata
        meta = {
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df)),
            "period": "Periodic"
        }
        
        # Build payload
        payload = gen.build_payload(
            alerts=alerts,
            signals=signals,
            subgroups=subgroups if subgroups else None,
            lot_findings=lot_findings if lot_findings else None,
            narrative_highlights=narrative_highlights if narrative_highlights else None,
            meta=meta
        )
        
        # Generate PBRER (heavy mode)
        with st.spinner("📙 Generating Periodic Benefit-Risk Evaluation Report (PBRER)... This may take 30-60 seconds."):
            pbrer_content = gen.generate_pbrer(payload, heavy=True)
        
        if pbrer_content:
            # Store in session state
            st.session_state["pbrer_report"] = {
                "content": pbrer_content,
                "meta": meta,
                "generated_on": datetime.now().isoformat(),
                "payload": payload
            }
            st.success("✅ PBRER report generated successfully! View it in the 'DSUR / PBRER' tab.")
            st.info("💡 The PBRER includes comprehensive analysis according to ICH E2C(R2) guidelines.")
        else:
            st.error("❌ Failed to generate PBRER report. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating PBRER: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_capa_recommendations(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate CAPA (Corrective and Preventive Actions) recommendations from trend alerts (CHUNK 6.15).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.capa_recommendations import CAPAEngine
        from datetime import datetime
        
        capa_engine = CAPAEngine()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        rpf_ranked = alerts.get("rpf_ranked", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
            if alert.get("subgroups"):
                subgroups.update(alert.get("subgroups", {}))
            if alert.get("lot_alerts"):
                lot_findings.extend(alert.get("lot_alerts", []))
            if alert.get("narrative_clusters"):
                narrative_highlights.extend(alert.get("narrative_clusters", []))
        
        # Build metadata
        meta = {
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df))
        }
        
        # Build payload
        payload = capa_engine.build_payload(
            alerts=alerts,
            signals=signals,
            rpf_ranked=rpf_ranked,
            subgroups=subgroups if subgroups else None,
            lot_findings=lot_findings if lot_findings else None,
            narrative_highlights=narrative_highlights if narrative_highlights else None,
            meta=meta
        )
        
        # Generate CAPA (heavy mode)
        with st.spinner("🛠️ Generating CAPA Recommendations... This may take 30-60 seconds."):
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
            st.success("✅ CAPA recommendations generated successfully! View them in the 'CAPA' tab.")
            st.info("💡 The CAPA includes corrective actions, preventive measures, regulatory notifications, and inspection readiness guidance.")
        else:
            st.error("❌ Failed to generate CAPA recommendations. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating CAPA: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_inspection_readiness(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Inspection Readiness package from trend alerts (CHUNK 6.16).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.inspection_readiness_engine import InspectionReadinessEngine
        from src.audit_trail import read_audit_log
        from datetime import datetime
        
        inspection_engine = InspectionReadinessEngine()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        rpf_ranked = alerts.get("rpf_ranked", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
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
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df))
        }
        
        # Build payload
        payload = inspection_engine.build_payload(
            alerts=alerts,
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
        with st.spinner("📑 Generating Inspection Readiness Package... This may take 30-60 seconds."):
            evidence_pack = inspection_engine.generate_evidence_pack(payload, audit_trail, heavy=True)
            
            # Generate inspector questions (default to FDA)
            inspector_questions = inspection_engine.generate_inspector_questions(
                {"signals": signals, "rpf_ranked": rpf_ranked},
                agency="FDA"
            )
        
        if evidence_pack:
            # Store in session state
            st.session_state["inspection_readiness"] = {
                "evidence_pack": evidence_pack,
                "inspector_questions": inspector_questions or "",
                "meta": meta,
                "generated_on": datetime.now().isoformat(),
                "agency": "FDA",
                "payload": payload
            }
            st.success("✅ Inspection Readiness Package generated successfully! View it in the 'Inspection' tab.")
            st.info("💡 The package includes complete evidence documentation, audit trail summary, and simulated inspector questions for regulatory compliance.")
        else:
            st.error("❌ Failed to generate Inspection Readiness Package. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating Inspection Readiness Package: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_csp(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Core Safety Profile (CSP) from trend alerts (CHUNK 6.18).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.csp_generator import CSPGenerator
        from datetime import datetime
        
        csp_engine = CSPGenerator()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        rpf_ranked = alerts.get("rpf_ranked", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
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
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df))
        }
        
        # Build payload
        payload = csp_engine.build_payload(
            alerts=alerts,
            signals=signals,
            rpf_ranked=rpf_ranked,
            subgroups=subgroups if subgroups else None,
            lot_findings=lot_findings if lot_findings else None,
            narrative_highlights=narrative_highlights if narrative_highlights else None,
            meta=meta,
            benefit_risk=benefit_risk
        )
        
        # Determine version (increment if CSP exists)
        existing_csp = st.session_state.get("csp_profile")
        version = "1.0"
        if existing_csp:
            try:
                prev_version = float(existing_csp.get("version", "1.0"))
                version = f"{prev_version + 0.1:.1f}"
            except Exception:
                version = "1.0"
        
        # Generate CSP (heavy mode)
        with st.spinner("🧬 Generating Core Safety Profile (CSP)... This may take 30-60 seconds."):
            csp_content = csp_engine.generate_csp(payload, heavy=True)
        
        if csp_content:
            # Store in session state
            st.session_state["csp_profile"] = {
                "content": csp_content,
                "meta": meta,
                "generated_on": datetime.now().isoformat(),
                "version": version,
                "payload": payload
            }
            st.success(f"✅ Core Safety Profile (CSP) generated successfully! Version {version}. View it in the 'CSP' tab.")
            st.info("💡 The CSP includes Important Identified Risks, Important Potential Risks, Missing Information, and recommended CCDS wording aligned with EMA RMP Annex 1 and ICH E2C(R2).")
        else:
            st.error("❌ Failed to generate Core Safety Profile. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating Core Safety Profile: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _generate_label_impact(normalized_df: pd.DataFrame, alerts_result: Dict[str, Any]):
    """
    Generate Label Impact Assessment from trend alerts (CHUNK 6.19).
    
    Args:
        normalized_df: DataFrame with PV data
        alerts_result: Trend alerts result dictionary
    """
    try:
        from src.ai.label_impact_engine import LabelImpactEngine
        from datetime import datetime
        
        label_engine = LabelImpactEngine()
        
        # Extract data from alerts
        alerts = alerts_result
        signals = alerts.get("emerging_signals", [])
        rpf_ranked = alerts.get("rpf_ranked", [])
        
        # Extract subgroup and lot data from alerts
        subgroups = {}
        lot_findings = []
        narrative_highlights = []
        
        # Collect from individual alerts
        for alert in alerts.get("alerts", []):
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
            "drug": "Multiple Drugs",
            "reaction": "Multiple Reactions",
            "total_cases": alerts.get("meta", {}).get("total_cases", len(normalized_df))
        }
        
        # Build payload
        payload = label_engine.build_payload(
            alerts=alerts,
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
        with st.spinner("📄 Generating Label Impact Assessment... This may take 30-60 seconds."):
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
            st.success(f"✅ Label Impact Assessment generated successfully! Impact Level: {impact_level}. View it in the 'Label Impact' tab.")
            st.info("💡 The assessment includes proposed EMA SmPC and FDA USPI changes, CCDS updates, regulatory justification, and reviewer notes for QPPV & Safety Review Committee. All changes require regulatory approval before implementation.")
        else:
            st.error("❌ Failed to generate Label Impact Assessment. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error generating Label Impact Assessment: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

