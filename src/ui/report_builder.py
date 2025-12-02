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
from src.org.org_profile_manager import get_current_tenant_id
from src.auth.auth import get_current_user

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
    
    # Get tenant ID for multi-tenant support
    tenant_id = get_current_tenant_id()
    current_user = get_current_user()
    
    # Show warnings if org config is missing
    if report_type in ["PSUR", "DSUR"]:
        from src.org.org_profile_manager import load_org_product_config
        org_config = load_org_product_config(tenant_id=tenant_id, product=drug)
        if not org_config:
            st.info(
                f"💡 **Tip:** Configure your organization's regulatory settings for {drug} to populate "
                f"organization-specific sections (Marketing Authorization, Safety Actions, RMP Changes, etc.). "
                f"Go to **Org Profile Settings** to configure."
            )
    
    # Generate report
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner("Generating regulatory report..."):
            try:
                if report_type == "PSUR":
                    # Generate PSUR with real data (no need for data_sources parameter)
                    # Use max.time() for period_end to include the full end date
                    report = psur_generator.generate_psur(
                        drug=drug,
                        period_start=datetime.combine(period_start, datetime.min.time()),
                        period_end=datetime.combine(period_end, datetime.max.time()),
                        tenant_id=tenant_id
                    )
                    
                    st.session_state["generated_report"] = report
                    st.session_state["report_type"] = "PSUR"
                
                elif report_type == "DSUR":
                    # Generate DSUR with real data
                    # Use max.time() for period_end to include the full end date
                    report = dsur_generator.generate_dsur(
                        drug=drug,
                        period_start=datetime.combine(period_start, datetime.min.time()),
                        period_end=datetime.combine(period_end, datetime.max.time()),
                        tenant_id=tenant_id
                    )
                    
                    st.session_state["generated_report"] = report
                    st.session_state["report_type"] = "DSUR"
                
                else:  # Signal Report
                    # Try to get real signal data from session state
                    signal_data = st.session_state.get("current_signal", {})
                    
                    # If no current signal, try to get from governance signals
                    if not signal_data:
                        governance_signals = st.session_state.get("governance_signals", [])
                        if governance_signals:
                            # Find matching signal
                            for sig in governance_signals:
                                if (sig.get("drug", "").lower() == drug.lower() and 
                                    sig.get("reaction", "").lower() == reaction.lower()):
                                    signal_data = sig
                                    break
                    
                    # If still no signal data, create minimal structure from user input
                    if not signal_data:
                        st.warning(
                            f"⚠️ No active signal found for {drug} → {reaction}. "
                            f"Using basic structure. For full signal analysis, select a signal from the "
                            f"Trend Alerts or Governance Dashboard first."
                        )
                        signal_data = {
                            "signal_id": f"SIGNAL-{drug[:3].upper()}-{reaction[:3].upper()}",
                            "drug": drug,
                            "reaction": reaction,
                            "quantum_score": 0.0,
                            "gri_score": 0.0,
                            "priority_category": "unknown",
                            "sources": [],
                            "faers_count": 0,
                            "social_count": 0,
                            "literature_count": 0,
                            "clinical_count": 0
                        }
                    
                    report = signal_generator.generate_signal_report(
                        drug=drug,
                        reaction=reaction,
                        signal_data=signal_data,
                        tenant_id=tenant_id
                    )
                    
                    st.session_state["generated_report"] = report
                    st.session_state["report_type"] = "Signal Report"
                
                st.success("✅ Report generated")
                
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                st.error(f"❌ Error generating report: {str(e)}")
                st.info("💡 Check logs for details. Ensure data sources are properly configured.")
    
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

