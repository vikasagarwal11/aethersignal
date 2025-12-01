"""
PSUR/DSUR Report Builder UI (Phase 3I.6)
Interactive UI for generating and editing regulatory reports.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.reports.psur_generator import PSURGenerator, DSURGenerator, SignalReportGenerator
from src.reports.ai_narrative_writer import AINarrativeWriter

logger = logging.getLogger(__name__)


def render_report_builder():
    """Render PSUR/DSUR report builder UI."""
    st.header("📄 Regulatory Report Builder")
    st.caption("Automated PSUR, DSUR, and Signal Evaluation Report generation")
    
    # Initialize generators
    psur_generator = PSURGenerator()
    dsur_generator = DSURGenerator()
    signal_generator = SignalReportGenerator()
    narrative_writer = AINarrativeWriter()
    
    # Report type selector
    report_type = st.selectbox(
        "Report Type",
        options=["PSUR", "DSUR", "Signal Evaluation Report"]
    )
    
    # Common inputs
    col1, col2 = st.columns(2)
    with col1:
        drug = st.text_input("Drug", "Semaglutide")
    with col2:
        if report_type == "PSUR" or report_type == "DSUR":
            period_start = st.date_input("Period Start", datetime.now() - timedelta(days=365))
            period_end = st.date_input("Period End", datetime.now())
        else:
            reaction = st.text_input("Reaction", "Nausea")
    
    # Generate report
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner("Generating regulatory report..."):
            if report_type == "PSUR":
                # Get data sources (placeholder - would query unified database)
                data_sources = {
                    "signals": [],
                    "faers": [],
                    "social": [],
                    "literature": []
                }
                
                report = psur_generator.generate_psur(
                    drug,
                    datetime.combine(period_start, datetime.min.time()),
                    datetime.combine(period_end, datetime.min.time()),
                    data_sources
                )
                
                st.session_state["generated_report"] = report
                st.session_state["report_type"] = "PSUR"
            
            elif report_type == "DSUR":
                data_sources = {
                    "signals": [],
                    "clinical_trials": []
                }
                
                report = dsur_generator.generate_dsur(
                    drug,
                    datetime.combine(period_start, datetime.min.time()),
                    datetime.combine(period_end, datetime.min.time()),
                    data_sources
                )
                
                st.session_state["generated_report"] = report
                st.session_state["report_type"] = "DSUR"
            
            else:  # Signal Report
                signal_data = {
                    "signal_id": "SIGNAL-001",
                    "quantum_score": 0.75,
                    "gri_score": 0.68,
                    "priority_category": "high",
                    "sources": ["faers", "social", "pubmed"],
                    "total_cases": 150
                }
                
                report = signal_generator.generate_signal_report(
                    drug, reaction, signal_data
                )
                
                st.session_state["generated_report"] = report
                st.session_state["report_type"] = "Signal Report"
            
            st.success("✅ Report generated")
    
    # Display report
    if "generated_report" in st.session_state:
        report = st.session_state["generated_report"]
        report_type = st.session_state.get("report_type", "Report")
        
        st.markdown("---")
        st.subheader(f"📄 {report_type}")
        
        # Report sections
        if "sections" in report:
            for section_key, section_data in report["sections"].items():
                with st.expander(section_data.get("title", section_key.replace("_", " ").title())):
                    if isinstance(section_data, dict):
                        if "content" in section_data:
                            st.write(section_data["content"])
                        elif "signals" in section_data:
                            signals_df = pd.DataFrame(section_data["signals"])
                            st.dataframe(signals_df, use_container_width=True)
                    else:
                        st.write(str(section_data))
        
        # Annexes
        if "annexes" in report:
            st.markdown("### Annexes")
            for annex_key, annex_content in report["annexes"].items():
                st.write(f"**{annex_key.replace('_', ' ').title()}:** {annex_content}")
        
        # Export options
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button("📄 PDF", "PDF export coming soon", disabled=True)
        with col2:
            st.download_button("📝 DOCX", "DOCX export coming soon", disabled=True)
        with col3:
            import json
            st.download_button(
                "📊 JSON",
                json.dumps(report, indent=2).encode(),
                file_name=f"{report_type.lower()}.json"
            )
        with col4:
            st.download_button("🌐 HTML", "HTML export coming soon", disabled=True)

