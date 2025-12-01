"""
Label Impact Assessment Panel for AetherSignal Results Display.
CHUNK 6.19: Regulatory-compliant label change recommendations for SmPC (EMA), USPI (FDA), and CCDS formats.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_label_impact_panel(label_impact_data: Optional[Dict[str, Any]] = None):
    """
    Render Label Impact Assessment panel (CHUNK 6.19).
    
    Args:
        label_impact_data: Dictionary containing label impact assessment data
    """
    if label_impact_data is None:
        # Try to get from session state
        label_impact_data = st.session_state.get("label_impact_assessment")
    
    if not label_impact_data:
        st.info("📄 **No Label Impact Assessment available.**")
        st.markdown("""
        To generate a Label Impact Assessment:
        
        1. **Via Chat:** Type "Does this signal require a label update?", "Draft EU SmPC warnings for this risk", or "Create USPI wording for anaphylaxis risk"
        2. **Via Button:** Click "📄 Label Impact" in the Trend Alerts tab (if available)
        3. **Via Query:** Ask "Is [reaction] an important identified risk that goes to Section 4.4?" or "Generate CCDS safety wording"
        
        The Label Impact Assessment will include:
        - Executive Summary with regulatory urgency
        - Proposed EMA SmPC Changes (Sections 4.3, 4.4, 4.5, 4.6, 4.8, 5.1/5.2)
        - Proposed FDA USPI Changes (Boxed Warning, Warnings & Precautions, Adverse Reactions, Drug Interactions, Use in Specific Populations)
        - CCDS / CCSI Updates
        - Regulatory Justification
        - Impact Assessment Ranking (High/Medium/Low/No Impact)
        - Reviewer Notes for QPPV & Safety Review Committee
        
        All recommendations follow EMA QRD template v10+ and FDA Physician Labeling Rule (PLR) requirements.
        """)
        return
    
    # Extract label impact content
    content = label_impact_data.get("content", "")
    meta = label_impact_data.get("meta", {})
    generated_on = label_impact_data.get("generated_on", datetime.now().isoformat())
    impact_level = label_impact_data.get("impact_level", "Not Assessed")
    
    if not content:
        st.warning("Label Impact Assessment content is empty. Please regenerate.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("📄 Label Impact Assessment")
    st.caption("Regulatory-compliant label change recommendations for SmPC (EMA), USPI (FDA), and CCDS formats")
    
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
        # Color-code impact level
        if impact_level == "High Impact":
            st.metric("Impact Level", "🔴 High")
        elif impact_level == "Medium Impact":
            st.metric("Impact Level", "🟠 Medium")
        elif impact_level == "Low Impact":
            st.metric("Impact Level", "🟡 Low")
        elif impact_level == "No Impact":
            st.metric("Impact Level", "⚪ None")
        else:
            st.metric("Impact Level", impact_level)
    
    # Important regulatory note
    st.warning("⚠️ **Regulatory Note:** All proposed label changes require QPPV review, Safety Review Committee approval, and regulatory agency submission. This assessment provides AI-generated recommendations based on detected signals. Human medical judgment and regulatory expertise are essential before implementation.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabs for different label formats
    tab1, tab2, tab3 = st.tabs(["📋 Full Assessment", "🇪🇺 EMA SmPC", "🇺🇸 FDA USPI"])
    
    # Tab 1: Full Assessment
    with tab1:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### Complete Label Impact Assessment")
        st.caption("Comprehensive assessment including all formats and regulatory justification")
        
        # Render markdown content
        st.markdown(content)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tab 2: EMA SmPC Focus
    with tab2:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### EMA SmPC Proposed Changes")
        st.caption("Summary of proposed changes aligned with EMA QRD template")
        
        # Extract SmPC sections if available (would require parsing, but showing full content for now)
        st.markdown("*Full assessment includes detailed SmPC section recommendations. View in Full Assessment tab.*")
        
        # Show summary from content if it contains SmPC sections
        if "Section 4.3" in content or "Section 4.4" in content:
            st.info("✅ SmPC section recommendations are included in the full assessment above.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tab 3: FDA USPI Focus
    with tab3:
        st.markdown("<div class='block-card'>", unsafe_allow_html=True)
        st.markdown("### FDA USPI Proposed Changes")
        st.caption("Summary of proposed changes aligned with FDA Physician Labeling Rule (PLR)")
        
        # Extract USPI sections if available
        st.markdown("*Full assessment includes detailed USPI section recommendations. View in Full Assessment tab.*")
        
        if "Boxed Warning" in content or "Warnings and Precautions" in content:
            st.info("✅ USPI section recommendations are included in the full assessment above.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Priority signals summary
    payload = label_impact_data.get("payload", {})
    if payload:
        rpf_ranked = payload.get("rpf_ranked", [])
        if rpf_ranked:
            st.markdown("---")
            st.markdown("### 📊 Associated Priority Signals")
            
            # Group by risk level
            critical = [e for e in rpf_ranked if e.get("risk_level") == "Critical"]
            high = [e for e in rpf_ranked if e.get("risk_level") == "High"]
            
            if critical or high:
                st.warning(f"⚠️ **{len(critical)} Critical** and **{len(high)} High** priority signals may require urgent label updates.")
            
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
                else:
                    st.markdown(f"{idx}. {risk_level}: {drug_sig} → {reaction_sig} (RPF Score: {rpf_score:.1f})")
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("💡 This Label Impact Assessment is AI-generated based on detected signals, CSP, and risk assessments. All proposed changes require QPPV review, SRC approval, and regulatory agency submission. Ensure alignment with current labeling and regulatory requirements before implementation.")
    with col2:
        # Create downloadable text file
        label_text = f"""
LABEL IMPACT ASSESSMENT
Generated: {generated_on}
Impact Level: {impact_level}
Drug: {drug}
Reaction: {reaction}

{content}
        """
        file_name = f"LabelImpact_{drug}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="📥 Download Assessment",
            data=label_text,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True
        )
    
