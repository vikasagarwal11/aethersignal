"""
Signal File Builder UI (CHUNK A8)
Complete inspector-ready narrative generator and signal file builder.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from src.ai.signal_file_generator import SignalFileGenerator
    GENERATORS_AVAILABLE = True
except ImportError:
    GENERATORS_AVAILABLE = False

try:
    from src.ai.governance_pdf_generator import GovernancePDFGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError:
    PDF_GENERATOR_AVAILABLE = False

try:
    from src.ai.governance_docx_generator import GovernanceDOCXGenerator
    DOCX_GENERATOR_AVAILABLE = True
except ImportError:
    DOCX_GENERATOR_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def render_signal_file_builder(
    drug: str,
    reaction: str,
    normalized_df: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    medical_llm = None
) -> None:
    """
    Render complete Signal File Builder UI (CHUNK A8.1).
    
    Args:
        drug: Drug name
        reaction: Adverse reaction/event
        normalized_df: Normalized DataFrame with case data
        signals: List of signal dictionaries
        trend_alerts: Trend alerts for this signal
        medical_llm: LLM instance for narrative generation
    """
    signal_key = f"{drug}-{reaction}"
    
    # Initialize signal file storage in session state
    if "signal_file_builder" not in st.session_state:
        st.session_state["signal_file_builder"] = {}
    
    if signal_key not in st.session_state["signal_file_builder"]:
        st.session_state["signal_file_builder"][signal_key] = {
            "drug": drug,
            "reaction": reaction,
            "narrative": None,
            "evidence": {},
            "attachments": {},
            "generated_at": None
        }
    
    signal_file_data = st.session_state["signal_file_builder"][signal_key]
    
    st.markdown(f"## 📄 Signal File Builder — {drug} × {reaction}")
    st.caption("Generate a complete, inspector-ready signal file with narrative, evidence, and governance attachments.")
    
    # Tabs (CHUNK A8.1)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📘 Narrative Summary",
        "📊 Evidence & Trends",
        "📑 Governance Attachments",
        "📤 Export File"
    ])
    
    # ----------------------
    # TAB 1: Narrative Summary (CHUNK A8.2)
    # ----------------------
    with tab1:
        st.markdown("### 📘 Signal Narrative Summary")
        st.info("Generate a comprehensive narrative summary covering clinical insights, trend interpretation, risk assessment, and governance notes.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            generate_narrative = st.button(
                "🔄 Generate/Regenerate Narrative",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            clear_narrative = st.button(
                "🗑️ Clear",
                use_container_width=True
            )
        
        if clear_narrative:
            signal_file_data["narrative"] = None
            st.rerun()
        
        if generate_narrative:
            with st.spinner("Generating comprehensive signal narrative... This may take 30-60 seconds."):
                narrative = _generate_signal_narrative(
                    drug=drug,
                    reaction=reaction,
                    normalized_df=normalized_df,
                    signals=signals,
                    trend_alerts=trend_alerts,
                    medical_llm=medical_llm
                )
                
                if narrative:
                    signal_file_data["narrative"] = narrative
                    signal_file_data["generated_at"] = datetime.now().isoformat()
                    st.session_state["signal_file_builder"][signal_key] = signal_file_data
                    st.success("✅ Narrative generated successfully!")
        
        # Display narrative
        if signal_file_data.get("narrative"):
            st.markdown("---")
            st.markdown("### Generated Narrative")
            st.markdown(signal_file_data["narrative"])
            
            # Edit option
            with st.expander("✏️ Edit Narrative", expanded=False):
                edited_narrative = st.text_area(
                    "Narrative Text",
                    value=signal_file_data["narrative"],
                    height=400,
                    key=f"edit_narrative_{signal_key}"
                )
                if st.button("💾 Save Edits", key=f"save_narrative_{signal_key}"):
                    signal_file_data["narrative"] = edited_narrative
                    st.session_state["signal_file_builder"][signal_key] = signal_file_data
                    st.success("✅ Narrative saved!")
                    st.rerun()
        else:
            st.info("Click 'Generate/Regenerate Narrative' to create the signal narrative.")
    
    # ----------------------
    # TAB 2: Evidence & Trends (CHUNK A8.3)
    # ----------------------
    with tab2:
        st.markdown("### 📊 Evidence & Trends")
        
        # Find matching signal
        signal_data = None
        if signals:
            for sig in signals:
                if (sig.get("drug", "").lower() == drug.lower() and
                    (sig.get("reaction", "").lower() == reaction.lower() or
                     sig.get("event", "").lower() == reaction.lower())):
                    signal_data = sig
                    break
        
        # Trend Graph
        st.markdown("#### 📈 Trend Graph")
        if normalized_df is not None and not normalized_df.empty:
            _render_trend_chart(normalized_df, drug, reaction)
        else:
            st.info("No trend data available. Please load case data first.")
        
        st.markdown("---")
        
        # Subgroup Findings
        st.markdown("#### 👥 Subgroup Findings")
        if signal_data:
            subgroups = signal_data.get("subgroups", {})
            if subgroups:
                _render_subgroup_table(subgroups)
            else:
                st.info("No subgroup analysis available for this signal.")
        else:
            st.info("Signal data not available for subgroup analysis.")
        
        st.markdown("---")
        
        # Emerging Risks / Trend Alerts
        st.markdown("#### ⚠️ Emerging Risks & Trend Alerts")
        if trend_alerts:
            alert_df_data = []
            for alert in trend_alerts[:10]:  # Top 10
                if isinstance(alert, dict):
                    alert_df_data.append({
                        "Severity": alert.get("severity", "info"),
                        "Title": alert.get("title", "Alert"),
                        "Summary": alert.get("summary", "")[:100] + "..." if len(alert.get("summary", "")) > 100 else alert.get("summary", ""),
                        "Date": alert.get("date", "N/A")
                    })
            
            if alert_df_data:
                alert_df = pd.DataFrame(alert_df_data)
                st.dataframe(alert_df, use_container_width=True, hide_index=True)
        else:
            st.info("No trend alerts available for this signal.")
        
        st.markdown("---")
        
        # RPF Scores
        st.markdown("#### 🎛 Risk Prioritization Framework (RPF)")
        if signal_data:
            rpf_score = signal_data.get("rpf_score") or signal_data.get("qsp_score", 0)
            priority = signal_data.get("priority") or signal_data.get("qsp_priority", "Unknown")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("RPF Score", f"{rpf_score:.1f}" if isinstance(rpf_score, (int, float)) else "N/A")
            with col2:
                st.metric("Priority Level", priority)
        else:
            st.info("RPF scores not available for this signal.")
    
    # ----------------------
    # TAB 3: Governance Attachments (CHUNK A8.4)
    # ----------------------
    with tab3:
        st.markdown("### 📑 Governance Attachments")
        st.info("All governance artifacts and evidence included in this signal file.")
        
        # Check what's available
        attachments = {}
        
        # Trend Analysis
        attachments["Trend Analysis"] = trend_alerts is not None and len(trend_alerts) > 0
        
        # RPF Table
        attachments["RPF Table"] = signal_data is not None and signal_data.get("rpf_score") is not None
        
        # Benefit-Risk Summary
        attachments["Benefit–Risk Summary"] = signal_data is not None and signal_data.get("benefit_risk") is not None
        
        # Label Impact
        attachments["Label Impact"] = signal_data is not None and signal_data.get("label_impact") is not None
        
        # CAPA Recommendation
        attachments["CAPA Recommendation"] = signal_data is not None and signal_data.get("capa") is not None
        
        # Governance Checklist
        attachments["Governance Checklist"] = signal_data is not None and signal_data.get("governance_checklist") is not None
        
        # Subgroup Analysis
        attachments["Subgroup Analysis"] = signal_data is not None and signal_data.get("subgroups") is not None
        
        # Signal Confidence Score
        attachments["Signal Confidence Score"] = signal_data is not None and signal_data.get("confidence_score") is not None
        
        # Display attachment status
        st.markdown("#### Attachment Status")
        attachment_df = pd.DataFrame({
            "Attachment": list(attachments.keys()),
            "Status": ["✅ Available" if v else "❌ Missing" for v in attachments.values()]
        })
        st.dataframe(attachment_df, use_container_width=True, hide_index=True)
        
        # Summary
        available_count = sum(attachments.values())
        total_count = len(attachments)
        
        st.markdown("---")
        st.metric("Attachments Available", f"{available_count}/{total_count}")
        
        if available_count < total_count:
            st.warning(f"⚠️ {total_count - available_count} attachment(s) missing. Generate missing components to complete the signal file.")
        else:
            st.success("✅ All attachments available! Signal file is complete and ready for export.")
    
    # ----------------------
    # TAB 4: Export File (CHUNK A8.5)
    # ----------------------
    with tab4:
        st.markdown("### 📤 Export Signal File")
        st.info("Generate and download the complete signal file as PDF or DOCX for regulatory submission and audit documentation.")
        
        if not GENERATORS_AVAILABLE:
            st.error("Signal file generators not available. Please install required dependencies.")
            return
        
        # Find matching signal ID
        signal_id = None
        if signals:
            for sig in signals:
                if (sig.get("drug", "").lower() == drug.lower() and
                    (sig.get("reaction", "").lower() == reaction.lower() or
                     sig.get("event", "").lower() == reaction.lower())):
                    signal_id = sig.get("id") or sig.get("signal_id")
                    break
        
        if not signal_id:
            st.warning("⚠️ Signal ID not found. Cannot generate file. Please ensure signal is properly registered.")
            return
        
        col1, col2 = st.columns(2)
        
        # PDF Generation
        with col1:
            st.markdown("#### 📄 PDF Export")
            if st.button("Generate PDF", type="primary", use_container_width=True, key="gen_pdf"):
                with st.spinner("Generating PDF signal file..."):
                    try:
                        # Use SignalFileGenerator to get signal file data
                        if normalized_df is not None:
                            dataset = {"df": normalized_df, "signals": signals or []}
                            signal_file_gen = SignalFileGenerator(dataset)
                            signal_file_data_dict = signal_file_gen.generate_signal_file(signal_id)
                            
                            # Generate PDF
                            pdf_gen = GovernancePDFGenerator(dataset)
                            pdf_path = pdf_gen.generate_pdf(signal_id, f"/tmp/signal_file_{signal_key}.pdf")
                            
                            # Read PDF bytes
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                "📥 Download PDF",
                                pdf_bytes,
                                file_name=f"signal_file_{drug}_{reaction}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key="download_pdf"
                            )
                            st.success("✅ PDF generated successfully!")
                        else:
                            st.error("Normalized DataFrame required for PDF generation.")
                    except Exception as e:
                        st.error(f"❌ PDF generation error: {str(e)}")
        
        # DOCX Generation
        with col2:
            st.markdown("#### 📝 DOCX Export")
            if st.button("Generate DOCX", type="primary", use_container_width=True, key="gen_docx"):
                with st.spinner("Generating DOCX signal file..."):
                    try:
                        if normalized_df is not None:
                            dataset = {"df": normalized_df, "signals": signals or []}
                            signal_file_gen = SignalFileGenerator(dataset)
                            signal_file_data_dict = signal_file_gen.generate_signal_file(signal_id)
                            
                            # Generate DOCX
                            docx_gen = GovernanceDOCXGenerator(dataset)
                            docx_path = docx_gen.generate_docx(signal_id, f"/tmp/signal_file_{signal_key}.docx")
                            
                            # Read DOCX bytes
                            with open(docx_path, "rb") as f:
                                docx_bytes = f.read()
                            
                            st.download_button(
                                "📥 Download DOCX",
                                docx_bytes,
                                file_name=f"signal_file_{drug}_{reaction}_{datetime.now().strftime('%Y%m%d')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="download_docx"
                            )
                            st.success("✅ DOCX generated successfully!")
                        else:
                            st.error("Normalized DataFrame required for DOCX generation.")
                    except Exception as e:
                        st.error(f"❌ DOCX generation error: {str(e)}")
        
        st.markdown("---")
        st.caption("💡 Generated files include all governance attachments, narrative summary, evidence tables, and compliance checklists. Ready for regulatory submission and audit documentation.")


def _generate_signal_narrative(
    drug: str,
    reaction: str,
    normalized_df: Optional[pd.DataFrame],
    signals: Optional[List[Dict[str, Any]]],
    trend_alerts: Optional[List[Dict[str, Any]]],
    medical_llm
) -> Optional[str]:
    """Generate comprehensive signal narrative using LLM (CHUNK A8.2)."""
    if not LLM_AVAILABLE or medical_llm is None:
        return "AI narrative generation requires LLM availability."
    
    # Find signal data
    signal_data = None
    if signals:
        for sig in signals:
            if (sig.get("drug", "").lower() == drug.lower() and
                (sig.get("reaction", "").lower() == reaction.lower() or
                 sig.get("event", "").lower() == reaction.lower())):
                signal_data = sig
                break
    
    # Build comprehensive prompt
    prompt = f"""
You are a senior pharmacovigilance scientist preparing a comprehensive Signal File narrative.

SIGNAL: {drug} → {reaction}

SIGNAL DATA:
{_format_signal_data_for_prompt(signal_data)}

TREND ALERTS:
{_format_trend_alerts_for_prompt(trend_alerts)}

CASE COUNT: {len(normalized_df) if normalized_df is not None else 0}

Generate a professional, regulatory-ready narrative summary covering:

1. **Executive Summary**
   - Signal overview and clinical significance
   - Key risk indicators and priority level

2. **Clinical Context**
   - Relevant medical background
   - Mechanism of action considerations
   - Known class effects or literature support

3. **Trend Analysis & Emerging Risks**
   - Temporal patterns observed
   - Spike or anomaly detection findings
   - Risk acceleration or change-points

4. **Risk Prioritization**
   - RPF score and justification
   - Disproportionality strength
   - Seriousness impact assessment

5. **Subgroup Analysis**
   - Vulnerable populations identified
   - Age/sex/region patterns
   - Dose-response relationships

6. **Label Impact Considerations**
   - Current label status
   - Proposed updates or warnings
   - Regulatory implications

7. **Benefit-Risk Assessment**
   - Benefit-risk balance
   - Risk minimization considerations

8. **CAPA Recommendations**
   - Corrective actions needed
   - Preventive measures
   - Risk minimization strategies

9. **Governance & Compliance**
   - Timeline compliance status
   - Reviewer assignments
   - Documentation completeness

10. **Next Steps & Recommendations**
    - Recommended actions
    - Escalation needs
    - Follow-up requirements

Format as a professional, regulatory-compliant narrative suitable for:
- Signal File documentation
- Safety Review Committee presentation
- Regulatory submission (FDA/EMA)
- Audit documentation

Use formal, clinical language aligned with ICH E2C(R2), EMA GVP Module IX, and FDA guidance.
"""
    
    try:
        system_prompt = """You are a senior pharmacovigilance scientist and regulatory expert with expertise in:
- ICH E2C(R2) Periodic Benefit-Risk Evaluation Reports
- EMA GVP Module IX Signal Management
- FDA 21 CFR 314.80 Safety Reporting
- CIOMS VIII Signal Detection Guidelines

Generate inspection-ready, professional narratives for signal management documentation."""
        
        if callable(medical_llm):
            response = medical_llm(prompt, system_prompt)
        else:
            from src.ai.medical_llm import call_medical_llm
            response = call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="regulatory_writing",
                max_tokens=3000,
                temperature=0.3
            )
        
        return response
    except Exception as e:
        return f"Narrative generation error: {str(e)}"


def _format_signal_data_for_prompt(signal_data: Optional[Dict[str, Any]]) -> str:
    """Format signal data for LLM prompt."""
    if not signal_data:
        return "Signal data not available."
    
    return f"""
- RPF Score: {signal_data.get('rpf_score', signal_data.get('qsp_score', 'N/A'))}
- Priority: {signal_data.get('priority', signal_data.get('qsp_priority', 'Unknown'))}
- Confidence Score: {signal_data.get('confidence_score', signal_data.get('signal_confidence', 'N/A'))}
- Lifecycle Stage: {signal_data.get('lifecycle', signal_data.get('status', 'Unknown'))}
"""


def _format_trend_alerts_for_prompt(trend_alerts: Optional[List[Dict[str, Any]]]) -> str:
    """Format trend alerts for LLM prompt."""
    if not trend_alerts:
        return "No trend alerts available."
    
    alerts_text = []
    for alert in trend_alerts[:5]:  # Top 5
        if isinstance(alert, dict):
            alerts_text.append(f"- {alert.get('title', 'Alert')}: {alert.get('summary', '')}")
    
    return "\n".join(alerts_text) if alerts_text else "No trend alerts available."


def _render_trend_chart(normalized_df: pd.DataFrame, drug: str, reaction: str) -> None:
    """Render trend chart for signal."""
    try:
        import plotly.express as px
        
        # Filter for this signal
        drug_col = next((col for col in ["drug", "drug_name", "drug_concept_name"] if col in normalized_df.columns), None)
        reaction_col = next((col for col in ["reaction", "reaction_pt", "pt", "adverse_reaction", "event"] if col in normalized_df.columns), None)
        
        if drug_col and reaction_col:
            signal_df = normalized_df[
                (normalized_df[drug_col].astype(str).str.lower() == drug.lower()) &
                (normalized_df[reaction_col].astype(str).str.lower() == reaction.lower())
            ].copy()
            
            if not signal_df.empty:
                # Extract date column
                date_col = next((col for col in ["event_date", "report_date", "date", "received_date"] if col in signal_df.columns), None)
                
                if date_col:
                    signal_df[date_col] = pd.to_datetime(signal_df[date_col], errors='coerce')
                    signal_df = signal_df.dropna(subset=[date_col])
                    
                    if not signal_df.empty:
                        signal_df["year_month"] = signal_df[date_col].dt.to_period("M").astype(str)
                        monthly_counts = signal_df.groupby("year_month").size().reset_index(name="count")
                        monthly_counts = monthly_counts.sort_values("year_month")
                        
                        fig = px.line(
                            monthly_counts,
                            x="year_month",
                            y="count",
                            title=f"Case Count Trend: {drug} → {reaction}",
                            markers=True
                        )
                        fig.update_layout(xaxis_tickangle=-45, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        return
        
        st.info("Could not generate trend chart. Date column not found or insufficient data.")
    except Exception as e:
        st.warning(f"Trend chart generation error: {str(e)}")


def _render_subgroup_table(subgroups: Dict[str, Any]) -> None:
    """Render subgroup analysis table."""
    try:
        if isinstance(subgroups, dict) and subgroups:
            # Convert to DataFrame if possible
            subgroup_data = []
            for key, value in subgroups.items():
                if isinstance(value, dict):
                    subgroup_data.append({
                        "Subgroup": key,
                        "Count": value.get("count", value.get("cases", "N/A")),
                        "PRR": value.get("prr", "N/A"),
                        "Significance": value.get("significance", "N/A")
                    })
            
            if subgroup_data:
                subgroup_df = pd.DataFrame(subgroup_data)
                st.dataframe(subgroup_df, use_container_width=True, hide_index=True)
            else:
                st.json(subgroups)
        else:
            st.json(subgroups)
    except Exception:
        st.json(subgroups)

