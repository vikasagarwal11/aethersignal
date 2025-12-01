"""
Signal Governance Drill-Down Panel (CHUNK A7.2)
Interactive deep-dive panel for signal governance inspection.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.ai.lifecycle_inference import infer_lifecycle_stage
    from src.ai.signal_confidence import SignalConfidenceEngine
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    from src.ai.governance_engine import GovernanceEngine
    from src.ai.hybrid_summary_engine import HybridSummaryEngine
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False


def show_signal_governance_panel(
    drug: str,
    reaction: str,
    normalized_df: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    medical_llm = None
) -> None:
    """
    Display full signal governance drill-down panel (CHUNK A7.2).
    
    Args:
        drug: Drug name
        reaction: Adverse reaction/event
        normalized_df: Normalized DataFrame with case data
        signals: List of signal dictionaries
        trend_alerts: Trend alerts for this signal
        medical_llm: LLM instance for AI summaries
    """
    st.markdown(f"## 🗂 Signal Governance — {drug} × {reaction}")
    
    # Find matching signal data
    signal_data = None
    if signals:
        for sig in signals:
            if (sig.get("drug", "").lower() == drug.lower() and
                (sig.get("reaction", "").lower() == reaction.lower() or
                 sig.get("event", "").lower() == reaction.lower())):
                signal_data = sig
                break
    
    # Filter normalized_df for this signal
    signal_df = None
    if normalized_df is not None and not normalized_df.empty:
        drug_col = next((col for col in ["drug", "drug_name", "drug_concept_name"] if col in normalized_df.columns), None)
        reaction_col = next((col for col in ["reaction", "reaction_pt", "pt", "adverse_reaction", "event"] if col in normalized_df.columns), None)
        
        if drug_col and reaction_col:
            signal_df = normalized_df[
                (normalized_df[drug_col].astype(str).str.lower() == drug.lower()) &
                (normalized_df[reaction_col].astype(str).str.lower() == reaction.lower())
            ].copy()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Trend & Timeline",
        "🎛 Risk Profile",
        "🔄 Lifecycle",
        "📋 Case Details",
        "📄 Signal File Builder",
        "🧠 AI Summary"
    ])
    
    # ----------------------
    # TAB 1: Trend & Timeline
    # ----------------------
    with tab1:
        st.markdown("### 📈 Trend Snapshot")
        
        if signal_df is not None and not signal_df.empty:
            # Try to extract date column
            date_col = next((col for col in ["event_date", "report_date", "date", "received_date"] if col in signal_df.columns), None)
            
            if date_col:
                try:
                    signal_df[date_col] = pd.to_datetime(signal_df[date_col], errors='coerce')
                    signal_df = signal_df.dropna(subset=[date_col])
                    
                    if not signal_df.empty:
                        # Monthly trend
                        signal_df["year_month"] = signal_df[date_col].dt.to_period("M").astype(str)
                        monthly_counts = signal_df.groupby("year_month").size().reset_index(name="count")
                        monthly_counts = monthly_counts.sort_values("year_month")
                        
                        if PLOTLY_AVAILABLE:
                            fig = px.line(
                                monthly_counts,
                                x="year_month",
                                y="count",
                                title=f"Case Count Trend: {drug} → {reaction}",
                                markers=True
                            )
                            fig.update_layout(xaxis_tickangle=-45, height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.line_chart(monthly_counts.set_index("year_month"))
                except Exception as e:
                    st.warning(f"Could not generate trend chart: {str(e)}")
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cases", len(signal_df))
            with col2:
                serious_count = len(signal_df[signal_df.get("serious", pd.Series()).astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"])]) if "serious" in signal_df.columns else 0
                st.metric("Serious Cases", serious_count)
            with col3:
                fatal_count = len(signal_df[signal_df.get("outcome", pd.Series()).astype(str).str.lower().str.contains("fatal|death", na=False)]) if "outcome" in signal_df.columns else 0
                st.metric("Fatal Cases", fatal_count)
            with col4:
                st.metric("Date Range", f"{signal_df[date_col].min().date() if date_col and date_col in signal_df.columns else 'N/A'} to {signal_df[date_col].max().date() if date_col and date_col in signal_df.columns else 'N/A'}")
        else:
            st.info("No case data available for trend analysis.")
        
        # Trend Alerts Summary
        if trend_alerts:
            st.markdown("### ⚠️ Trend Alerts")
            for alert in trend_alerts[:5]:  # Top 5
                if isinstance(alert, dict):
                    severity = alert.get("severity", "info")
                    title = alert.get("title", "Trend Alert")
                    summary = alert.get("summary", "")
                    
                    if severity in ["high", "critical", "warning"]:
                        st.error(f"**{title}**: {summary}")
                    elif severity == "medium":
                        st.warning(f"**{title}**: {summary}")
                    else:
                        st.info(f"**{title}**: {summary}")
    
    # ----------------------
    # TAB 2: Risk Profile
    # ----------------------
    with tab2:
        st.markdown("### 🎛 Risk Prioritization Factors (RPF)")
        
        if signal_data:
            # RPF Scores
            rpf_score = signal_data.get("rpf_score") or signal_data.get("qsp_score", 0)
            priority = signal_data.get("priority") or signal_data.get("qsp_priority", "Unknown")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("RPF Score", f"{rpf_score:.1f}" if isinstance(rpf_score, (int, float)) else "N/A")
            with col2:
                st.metric("Priority Level", priority)
            
            # Sub-component scores
            if COMPONENTS_AVAILABLE:
                try:
                    risk_engine = RiskPrioritizationEngine()
                    rpf_details = risk_engine.score_signal(signal_data) if hasattr(risk_engine, 'score_signal') else {}
                    
                    if rpf_details:
                        st.markdown("#### RPF Component Breakdown")
                        rpf_df = pd.DataFrame({
                            "Component": list(rpf_details.get("scores", {}).keys()),
                            "Score": list(rpf_details.get("scores", {}).values())
                        })
                        st.dataframe(rpf_df, use_container_width=True, hide_index=True)
                except Exception:
                    pass
        
        st.markdown("### 🔍 Signal Confidence Score (SCS)")
        
        if signal_data and COMPONENTS_AVAILABLE:
            try:
                confidence_engine = SignalConfidenceEngine()
                scs = signal_data.get("confidence_score") or signal_data.get("signal_confidence", 0)
                
                scs_normalized = float(scs) / 100.0 if scs > 1 else float(scs)
                
                st.metric("Confidence Score", f"{scs_normalized:.2%}")
                
                if scs_normalized >= 0.75:
                    st.success("High confidence signal")
                elif scs_normalized >= 0.5:
                    st.warning("Moderate confidence signal")
                else:
                    st.error("Low confidence signal - requires additional validation")
            except Exception:
                st.info("Confidence score calculation unavailable.")
        else:
            st.info("Signal data not available for confidence scoring.")
    
    # ----------------------
    # TAB 3: Lifecycle
    # ----------------------
    with tab3:
        st.markdown("### 🔄 Governance Lifecycle")
        
        lifecycle_stage = signal_data.get("lifecycle") if signal_data else None
        
        if lifecycle_stage:
            st.info(f"**Current Stage:** {lifecycle_stage}")
        else:
            # Infer lifecycle stage
            if COMPONENTS_AVAILABLE and signal_data:
                try:
                    lifecycle_info = infer_lifecycle_stage(
                        trend_alerts=trend_alerts or [],
                        rpf_scores=signal_data,
                        confidence_scores=signal_data.get("confidence_score", {}),
                        label_impact_scores=signal_data.get("label_impact", {}),
                        capa_findings=signal_data.get("capa", {}),
                        governance_gaps={},
                        summary={},
                        medical_llm=medical_llm
                    )
                    st.info(f"**Inferred Stage:** {lifecycle_info.get('stage', 'Unknown')}")
                    st.caption(lifecycle_info.get('evidence', ''))
                except Exception:
                    st.info("Lifecycle inference unavailable.")
            else:
                st.info("Lifecycle information not available.")
        
        # Timeline status
        if signal_data:
            timeline_status = signal_data.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                st.markdown("#### Timeline Compliance")
                assessment_status = timeline_status.get("assessment_status", "Unknown")
                st.metric("Assessment Status", assessment_status)
    
    # ----------------------
    # TAB 4: Case Details
    # ----------------------
    with tab4:
        st.markdown("### 📋 Case Details")
        
        if signal_df is not None and not signal_df.empty:
            # Show key columns
            display_cols = []
            for col in ["case_id", "age", "sex", "country", "outcome", "serious"]:
                if col in signal_df.columns:
                    display_cols.append(col)
            
            if display_cols:
                st.dataframe(signal_df[display_cols].head(100), use_container_width=True)
            else:
                st.dataframe(signal_df.head(100), use_container_width=True)
            
            st.caption(f"Showing first 100 of {len(signal_df)} cases. Use filters for detailed analysis.")
        else:
            st.info("No case-level data available for this signal.")
    
    # ----------------------
    # TAB 5: Signal File Builder (CHUNK A8)
    # ----------------------
    # Note: Signal File Builder is a comprehensive tool, so we link to it
    st.markdown("---")
    if st.button("📄 Open Signal File Builder", type="primary", use_container_width=True):
        st.session_state["open_signal_file_builder"] = {"drug": drug, "reaction": reaction}
        st.rerun()
    
    # ----------------------
    # TAB 6: AI Summary (renumbered)
    # ----------------------
    with tab5:
        st.markdown("### 🧠 AI Governance Summary")
        
        if COMPONENTS_AVAILABLE and medical_llm:
            try:
                hybrid_engine = HybridSummaryEngine()
                
                # Build summary
                summary = {
                    "drug": drug,
                    "reaction": reaction,
                    "signal_data": signal_data or {},
                    "case_count": len(signal_df) if signal_df is not None else 0,
                    "trend_alerts": len(trend_alerts) if trend_alerts else 0,
                    "rpf_score": signal_data.get("rpf_score") if signal_data else None,
                    "lifecycle": lifecycle_stage
                }
                
                with st.spinner("Generating AI summary..."):
                    for chunk in hybrid_engine.interpret_summary_stream(summary, medical_llm=medical_llm):
                        st.markdown(chunk, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI summary generation error: {str(e)}")
        else:
            st.info("AI summary generation requires LLM availability.")


def render_drill_down_button(
    drug: str,
    reaction: str,
    normalized_df: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    key: Optional[str] = None
) -> bool:
    """
    Render drill-down button and handle click (CHUNK A7.3).
    
    Returns:
        True if button was clicked
    """
    button_key = key or f"drill_down_{drug}_{reaction}"
    
    if st.button("🔍 Drill Down", key=button_key):
        show_signal_governance_panel(
            drug=drug,
            reaction=reaction,
            normalized_df=normalized_df,
            signals=signals,
            trend_alerts=trend_alerts
        )
        return True
    
    return False

