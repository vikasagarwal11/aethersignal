"""
Core Safety Profile (CSP) Panel for AetherSignal Results Display.
CHUNK 6.18: Regulatory-compliant Core Safety Profile generation aligned with EMA RMP Annex 1, ICH E2C(R2), and CCDS standards.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_csp_panel(csp_data: Optional[Dict[str, Any]] = None):
    """
    Render Core Safety Profile (CSP) panel (CHUNK 6.18).
    
    Args:
        csp_data: Dictionary containing CSP data
    """
    if csp_data is None:
        # Try to get from session state
        csp_data = st.session_state.get("csp_profile")
    
    if not csp_data:
        st.info("🧬 **No Core Safety Profile (CSP) available.**")
        st.markdown("""
        To generate a Core Safety Profile:
        
        1. **Via Chat:** Type "Generate the CSP", "What are the important identified risks?", or "Generate the CCDS safety section"
        2. **Via Button:** Click "🧬 CSP" in the Trend Alerts tab (if available)
        3. **Via Query:** Ask "Is [reaction] an important identified risk?" or "What is missing information for this product?"
        
        The Core Safety Profile will include:
        - Important Identified Risks
        - Important Potential Risks
        - Missing Information
        - Other Medically Important Conditions
        - Scientific Rationale for Classification
        - Recommended CCDS Wording (SmPC/USPI style)
        - Summary Table for RMP/CCDS
        
        The CSP follows EMA RMP Annex 1 structure and ICH E2C(R2) guidelines.
        """)
        return
    
    # Extract CSP content
    content = csp_data.get("content", "")
    meta = csp_data.get("meta", {})
    generated_on = csp_data.get("generated_on", datetime.now().isoformat())
    version = csp_data.get("version", "1.0")
    
    if not content:
        st.warning("CSP content is empty. Please regenerate.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("🧬 Core Safety Profile (CSP)")
    st.caption("Company Core Safety Information aligned with EMA RMP Annex 1, ICH E2C(R2), and CCDS standards")
    
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
        st.metric("Version", version)
    
    # Important note
    st.info("💡 **Regulatory Note:** This CSP is generated from detected signals and risk assessments. Review and validate all classifications before regulatory submission. Ensure alignment with current labeling and RMP.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # CSP Content
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    # Render markdown content
    st.markdown("### Core Safety Profile Content")
    st.markdown(content)
    
    # Risk summary (if available in payload)
    payload = csp_data.get("payload", {})
    if payload:
        rpf_ranked = payload.get("rpf_ranked", [])
        if rpf_ranked:
            st.markdown("---")
            st.markdown("### 📊 Associated Priority Signals")
            
            # Group by risk level
            critical = [e for e in rpf_ranked if e.get("risk_level") == "Critical"]
            high = [e for e in rpf_ranked if e.get("risk_level") == "High"]
            medium = [e for e in rpf_ranked if e.get("risk_level") == "Medium"]
            
            if critical or high:
                st.warning(f"⚠️ **{len(critical)} Critical** and **{len(high)} High** priority signals require immediate attention.")
            
            # Show top signals
            for idx, entry in enumerate(rpf_ranked[:10], 1):
                signal = entry.get("signal", {})
                rpf_score = entry.get("rpf_score", 0)
                risk_level = entry.get("risk_level", "Unknown")
                drug_sig = signal.get("drug", "Unknown")
                reaction_sig = signal.get("reaction", "Unknown")
                
                # Color-code by risk level
                if risk_level == "Critical":
                    st.markdown(f"**{idx}. 🔴 {risk_level}: {drug_sig} → {reaction_sig}** (RPF Score: {rpf_score:.1f})")
                elif risk_level == "High":
                    st.markdown(f"**{idx}. 🟠 {risk_level}: {drug_sig} → {reaction_sig}** (RPF Score: {rpf_score:.1f})")
                elif risk_level == "Medium":
                    st.markdown(f"**{idx}. 🟡 {risk_level}: {drug_sig} → {reaction_sig}** (RPF Score: {rpf_score:.1f})")
                else:
                    st.markdown(f"{idx}. {risk_level}: {drug_sig} → {reaction_sig} (RPF Score: {rpf_score:.1f})")
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("💡 This CSP is AI-generated based on detected signals, trends, and risk assessments. Review and validate all content, classifications, and recommended label wording before regulatory use.")
    with col2:
        # Create downloadable text file
        csp_text = f"""
CORE SAFETY PROFILE (CSP)
Version: {version}
Generated: {generated_on}
Drug: {drug}
Reaction: {reaction}

{content}
        """
        file_name = f"CSP_{drug}_v{version}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="📥 Download CSP",
            data=csp_text,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

