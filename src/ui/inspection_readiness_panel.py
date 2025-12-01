"""
Inspection Readiness & Audit Defense Panel for AetherSignal Results Display.
CHUNK 6.16: Regulatory inspection evidence packages and audit defense documentation.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_inspection_readiness_panel(inspection_data: Optional[Dict[str, Any]] = None):
    """
    Render Inspection Readiness panel (CHUNK 6.16).
    
    Args:
        inspection_data: Dictionary containing inspection readiness data
    """
    if inspection_data is None:
        # Try to get from session state
        inspection_data = st.session_state.get("inspection_readiness")
    
    if not inspection_data:
        st.info("📑 **No inspection readiness package available.**")
        st.markdown("""
        To generate an inspection readiness evidence package:
        
        1. **Via Chat:** Type "Prepare audit binder", "Generate FDA inspection evidence", or "Simulate inspector questions"
        2. **Via Button:** Click "📑 Inspection" in the Trend Alerts tab
        3. **Via Query:** Ask "Show me the audit trail" or "Create inspection evidence pack"
        
        The inspection readiness package will include:
        - Introduction & Scope
        - Safety Dataset Description
        - Signal Management Approach
        - Disproportionality Methods
        - Signal Assessment Output
        - Subgroup Assessment
        - Lot/Batch Assessment
        - RPF Prioritization Decisions
        - CAPA Actions
        - Reviewer Rationale Logs
        - Audit Trail Summary
        - System Validation Notes
        """)
        return
    
    # Extract inspection content
    evidence_pack = inspection_data.get("evidence_pack", "")
    inspector_questions = inspection_data.get("inspector_questions", "")
    meta = inspection_data.get("meta", {})
    generated_on = inspection_data.get("generated_on", datetime.now().isoformat())
    agency = inspection_data.get("agency", "FDA")
    
    if not evidence_pack:
        st.warning("Inspection readiness content is empty. Please regenerate.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("📑 Inspection Readiness Package")
    st.caption(f"Regulatory inspection evidence package aligned with {agency} requirements")
    
    # Metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        drug = meta.get("drug", "Multiple Drugs")
        st.metric("Drug", drug)
    with col2:
        reaction = meta.get("reaction", "Multiple Reactions")
        st.metric("Reaction", reaction)
    with col3:
        try:
            gen_date = datetime.fromisoformat(generated_on.replace('Z', '+00:00'))
            st.metric("Generated", gen_date.strftime("%Y-%m-%d %H:%M"))
        except Exception:
            st.metric("Generated", "N/A")
    with col4:
        st.metric("Agency", agency)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabs for Evidence Pack and Inspector Questions
    tab1, tab2 = st.tabs(["📋 Evidence Package", "❓ Inspector Q&A Simulation"])
    
    # Tab 1: Evidence Package
    with tab1:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### Inspection Readiness Evidence Package")
        st.caption("Complete documentation package for regulatory inspection")
        
        # Render markdown content
        st.markdown(evidence_pack)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tab 2: Inspector Questions
    with tab2:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### Simulated Inspector Questions")
        st.caption(f"Realistic {agency} inspector questions for preparation")
        
        if inspector_questions:
            st.markdown(inspector_questions)
        else:
            st.info("💡 Inspector questions simulation can be generated from the Trend Alerts tab.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("💡 This inspection readiness package is generated for regulatory compliance. Review and validate all evidence before regulatory submission.")
    with col2:
        # Create downloadable text file
        inspection_text = f"""
INSPECTION READINESS EVIDENCE PACKAGE
Generated: {generated_on}
Agency: {agency}
Drug: {drug}
Reaction: {reaction}

EVIDENCE PACKAGE
{evidence_pack}

INSPECTOR QUESTIONS
{inspector_questions if inspector_questions else "Not generated"}
        """
        file_name = f"Inspection_{agency}_{drug}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="📥 Download Package",
            data=inspection_text,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True
        )

