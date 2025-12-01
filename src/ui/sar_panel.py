"""
Safety Assessment Report (SAR) Panel for AetherSignal Results Display.
CHUNK 6.13: Full SAR report display with regulatory formatting.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_sar_panel(sar_data: Optional[Dict[str, Any]] = None):
    """
    Render Safety Assessment Report (SAR) panel (CHUNK 6.13).
    
    Args:
        sar_data: Dictionary containing SAR report data
    """
    if sar_data is None:
        # Try to get from session state
        sar_data = st.session_state.get("sar_report")
    
    if not sar_data:
        st.info("📄 **No SAR report available.**")
        st.markdown("""
        To generate a Safety Assessment Report:
        
        1. **Via Chat:** Type "Generate SAR" or "Create safety assessment report"
        2. **Via Button:** Click "📄 Generate Full SAR Report" in the Trend Alerts tab
        3. **Via Query:** Ask "What should I review first?" to trigger RPF analysis
        
        The SAR will include:
        - Executive Summary
        - Signal Overview
        - RPF Ranking & Justification
        - Trend Analysis
        - Subgroup Patterns
        - Lot/Batch Risk Assessment
        - Narrative Case Highlights
        - Recommended Actions
        - Regulatory Considerations
        """)
        return
    
    # Extract SAR content
    content = sar_data.get("content", "")
    meta = sar_data.get("meta", {})
    generated_on = sar_data.get("generated_on", datetime.now().isoformat())
    
    if not content:
        st.warning("SAR report content is empty. Please regenerate the report.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("📄 Safety Assessment Report (SAR)")
    
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
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # SAR Content
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    # Render markdown content
    st.markdown(content)
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("💡 This SAR is generated using FDA/EMA-aligned methodology. Review and validate before regulatory submission.")
    with col2:
        # Create downloadable text file
        sar_text = f"""
SAFETY ASSESSMENT REPORT (SAR)
Generated: {generated_on}
Drug: {drug}
Reaction: {reaction}

{content}
        """
        st.download_button(
            label="📥 Download SAR",
            data=sar_text,
            file_name=f"SAR_{drug}_{reaction}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

