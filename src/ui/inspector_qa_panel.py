"""
Inspector Q&A Simulation Panel (CHUNK 6.21.1 - Part 24)
Streamlit UI for inspector Q&A simulation and mock inspection reports.
"""
import datetime
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

try:
    from src.ai.inspector_qa_simulation import InspectorQASimulation, InspectorStyle
    INSPECTOR_QA_AVAILABLE = True
except ImportError:
    INSPECTOR_QA_AVAILABLE = False


def render_inspector_qa_tab(signals: Optional[List[Dict[str, Any]]] = None,
                           governance_package: Optional[Dict[str, Any]] = None,
                           df: Optional[pd.DataFrame] = None) -> None:
    """
    Render Inspector Q&A Simulation tab.
    
    Args:
        signals: List of signal dictionaries
        governance_package: Complete governance package
        df: Optional DataFrame for extracting signals if not provided
    """
    if not INSPECTOR_QA_AVAILABLE:
        st.error("Inspector Q&A Simulation Engine not available. Please install required dependencies.")
        return
    
    st.subheader("🔍 Inspector Q&A Simulation")
    
    st.markdown("""
    Simulate regulatory inspector interviews with FDA, EMA, MHRA, or PMDA styles.
    Generate realistic questions, evidence-linked responses, and full inspection reports.
    """)
    
    # Extract signals from DataFrame if not provided
    if signals is None and df is not None and not df.empty:
        signals = _extract_signals_from_df(df)
    
    if not signals:
        st.warning("No signals available for inspection simulation. Please load data and generate signals first.")
        return
    
    # Inspector style selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        inspector_style = st.selectbox(
            "Select Inspector Style:",
            ["fda", "ema", "mhra", "pmda", "general"],
            index=4,
            format_func=lambda x: x.upper() if x != "general" else "General"
        )
    
    with col2:
        num_questions = st.number_input(
            "Number of Questions:",
            min_value=5,
            max_value=30,
            value=15,
            step=5
        )
    
    # Initialize inspector simulation
    style_enum = InspectorStyle[inspector_style.upper()] if inspector_style != "general" else InspectorStyle.GENERAL
    inspector = InspectorQASimulation(style=style_enum)
    
    # Generate inspection session
    if st.button("🎯 Start Inspection Simulation", type="primary"):
        with st.spinner(f"Generating {inspector_style.upper()} inspection session with {num_questions} questions..."):
            inspection_session = inspector.simulate_inspection_session(
                signals=signals,
                governance_package=governance_package,
                num_questions=num_questions
            )
            
            # Store in session state
            st.session_state.inspection_session = inspection_session
    
    # Display inspection session if available
    if "inspection_session" in st.session_state:
        session = st.session_state.inspection_session
        
        # Session summary
        st.markdown("### 📋 Inspection Session Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", session.get("total_questions", 0))
        with col2:
            st.metric("Signals Reviewed", session.get("signals_reviewed", 0))
        with col3:
            st.metric("Inspector Style", session.get("style", "").upper())
        
        # Questions and Answers
        st.markdown("### 💬 Questions & Answers")
        
        questions = session.get("questions", [])
        if questions:
            for i, qa in enumerate(questions, 1):
                with st.expander(f"Q{i}: {qa.get('question', 'Question')}", expanded=(i <= 3)):
                    st.markdown(f"**Question:** {qa.get('question', 'N/A')}")
                    st.markdown(f"**Suggested Answer:**\n{qa.get('suggested_answer', qa.get('answer', 'N/A'))}")
                    
                    # Evidence references
                    evidence = qa.get("evidence_references", [])
                    if evidence:
                        st.markdown("**Evidence References:**")
                        for ref in evidence:
                            st.markdown(f"- {ref}")
                    
                    # SOP citations
                    sops = qa.get("sop_citations", [])
                    if sops:
                        st.markdown("**SOP Citations:**")
                        for sop in sops:
                            st.markdown(f"- {sop}")
                    
                    focus = qa.get("focus_area", "")
                    if focus:
                        st.caption(f"Focus Area: {focus}")
        
        # Session summary narrative
        summary = session.get("summary", "")
        if summary:
            st.markdown("### 📊 Session Summary")
            st.markdown(summary)
        
        # Generate Mock Inspection Report
        st.divider()
        st.markdown("### 📄 Mock Inspection Report")
        
        if st.button("📋 Generate Full Inspection Report", type="primary"):
            with st.spinner("Generating comprehensive inspection report..."):
                report = inspector.generate_mock_inspection_report(
                    inspection_session=session,
                    signals=signals,
                    governance_package=governance_package
                )
                
                st.session_state.inspection_report = report
        
        # Display inspection report if available
        if "inspection_report" in st.session_state:
            report = st.session_state.inspection_report
            
            st.markdown(f"#### {report.get('report_title', 'Inspection Report')}")
            st.caption(f"Generated: {report.get('date', 'N/A')}")
            
            # Executive Summary
            if report.get("executive_summary"):
                st.markdown("##### Executive Summary")
                st.markdown(report.get("executive_summary"))
            
            # Full Report
            if report.get("full_report"):
                with st.expander("📄 Full Inspection Report", expanded=False):
                    st.markdown(report.get("full_report"))
            
            # Findings
            findings = report.get("findings", [])
            if findings:
                st.markdown("##### Findings")
                for finding in findings:
                    st.markdown(f"- {finding}")
            
            # Recommendations
            recommendations = report.get("recommendations", [])
            if recommendations:
                st.markdown("##### Recommendations")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            
            # Evidence References
            evidence_refs = report.get("evidence_references", [])
            if evidence_refs:
                st.markdown("##### Evidence References")
                for ref in evidence_refs:
                    st.markdown(f"- {ref}")
            
            # SOP Citations
            sop_citations = report.get("sop_citations", [])
            if sop_citations:
                st.markdown("##### SOP Citations")
                for sop in sop_citations:
                    st.markdown(f"- {sop}")
            
            # Export options
            st.divider()
            st.markdown("### 💾 Export Report")
            
            # Create report text for export
            report_text = _format_report_for_export(report)
            
            st.download_button(
                label="📥 Download Report (TXT)",
                data=report_text,
                file_name=f"inspection_report_{report.get('date', datetime.datetime.now().strftime('%Y%m%d'))}.txt",
                mime="text/plain"
            )


def _extract_signals_from_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract signal-like structures from DataFrame."""
    if df is None or df.empty:
        return []
    
    signals = []
    
    # Detect column names
    drug_cols = ["drug", "drug_name", "drug_concept_name"]
    reaction_cols = ["reaction", "reaction_pt", "pt", "adverse_reaction"]
    serious_cols = ["serious", "seriousness", "serious_flag"]
    
    drug_col = next((col for col in drug_cols if col in df.columns), None)
    reaction_col = next((col for col in reaction_cols if col in df.columns), None)
    serious_col = next((col for col in serious_cols if col in df.columns), None)
    
    if not drug_col or not reaction_col:
        return []
    
    # Group by drug-reaction pairs
    grouped = df.groupby([drug_col, reaction_col])
    
    for (drug, reaction), group_df in grouped:
        total_cases = len(group_df)
        
        # Calculate serious cases
        if serious_col:
            serious_mask = group_df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"])
            serious_cases = serious_mask.sum()
        else:
            serious_cases = 0
        
        signal_dict = {
            "drug": drug,
            "reaction": reaction,
            "cases": total_cases,
            "serious_cases": serious_cases,
            "priority": "Medium"  # Default
        }
        
        signals.append(signal_dict)
    
    return signals


def _format_report_for_export(report: Dict[str, Any]) -> str:
    """Format inspection report for text export."""
    lines = []
    
    lines.append("=" * 80)
    lines.append(report.get("report_title", "Inspection Report"))
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Date: {report.get('date', 'N/A')}")
    lines.append(f"Inspector Style: {report.get('inspector_style', 'N/A').upper()}")
    lines.append("")
    
    # Executive Summary
    if report.get("executive_summary"):
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(report.get("executive_summary"))
        lines.append("")
    
    # Findings
    findings = report.get("findings", [])
    if findings:
        lines.append("FINDINGS")
        lines.append("-" * 80)
        for finding in findings:
            lines.append(f"- {finding}")
        lines.append("")
    
    # Recommendations
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")
    
    # Full Report
    if report.get("full_report"):
        lines.append("FULL REPORT")
        lines.append("-" * 80)
        lines.append(report.get("full_report"))
        lines.append("")
    
    # Evidence References
    evidence_refs = report.get("evidence_references", [])
    if evidence_refs:
        lines.append("EVIDENCE REFERENCES")
        lines.append("-" * 80)
        for ref in evidence_refs:
            lines.append(f"- {ref}")
        lines.append("")
    
    # SOP Citations
    sop_citations = report.get("sop_citations", [])
    if sop_citations:
        lines.append("SOP CITATIONS")
        lines.append("-" * 80)
        for sop in sop_citations:
            lines.append(f"- {sop}")
        lines.append("")
    
    return "\n".join(lines)

