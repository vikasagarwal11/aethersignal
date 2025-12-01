"""
DSUR (Development Safety Update Report) and PBRER (Periodic Benefit-Risk Evaluation Report) 
Panel for AetherSignal Results Display.
CHUNK 6.14: Full regulatory report display with ICH-compliant formatting.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_dsur_pbrer_panel(report_data: Optional[Dict[str, Any]] = None, report_type: str = "DSUR"):
    """
    Render DSUR or PBRER panel (CHUNK 6.14).
    
    Args:
        report_data: Dictionary containing report data
        report_type: "DSUR" or "PBRER"
    """
    if report_data is None:
        # Try to get from session state
        if report_type == "DSUR":
            report_data = st.session_state.get("dsur_report")
        else:
            report_data = st.session_state.get("pbrer_report")
    
    if not report_data:
        st.info(f"📘 **No {report_type} report available.**")
        st.markdown(f"""
        To generate a {report_type} report:
        
        1. **Via Chat:** Type "Generate {report_type}" or "Create {report_type.lower()} report"
        2. **Via Button:** Click "📘 Generate {report_type}" in the Trend Alerts tab
        3. **Via Query:** Ask "Generate regulatory report" or "Create benefit-risk evaluation"
        
        The {report_type} will include:
        - Executive Summary
        - Worldwide Marketing Approval Status
        - Safety Information Summary
        - Signal and Risk Evaluation
        - Benefit-Risk Assessment
        - Regulatory Actions and Recommendations
        """)
        return
    
    # Extract report content
    content = report_data.get("content", "")
    meta = report_data.get("meta", {})
    generated_on = report_data.get("generated_on", datetime.now().isoformat())
    
    if not content:
        st.warning(f"{report_type} report content is empty. Please regenerate the report.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    if report_type == "DSUR":
        st.subheader("📘 Development Safety Update Report (DSUR)")
        st.caption("ICH E2F Compliant - Annual report for ongoing clinical trials")
    else:
        st.subheader("📙 Periodic Benefit-Risk Evaluation Report (PBRER)")
        st.caption("ICH E2C(R2) Compliant - Post-marketing safety evaluation")
    
    # Metadata
    col1, col2, col3 = st.columns(3)
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
    
    # Report period (if available)
    period = meta.get("period", meta.get("report_period"))
    if period:
        st.caption(f"**Report Period:** {period}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Report Content
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    # Render markdown content
    st.markdown(content)
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        if report_type == "DSUR":
            st.caption("💡 This DSUR is generated according to ICH E2F guidelines. Review and validate before regulatory submission.")
        else:
            st.caption("💡 This PBRER is generated according to ICH E2C(R2) guidelines. Review and validate before regulatory submission.")
    with col2:
        # Create downloadable text file
        report_text = f"""
{report_type} REPORT
Generated: {generated_on}
Drug: {drug}
Reaction: {reaction}
Period: {period if period else "N/A"}

{content}
        """
        file_name = f"{report_type}_{drug}_{reaction}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label=f"📥 Download {report_type}",
            data=report_text,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

