"""
CAPA (Corrective and Preventive Actions) Recommendations Panel for AetherSignal Results Display.
CHUNK 6.15: AI-driven regulatory action recommendations for identified safety signals and risks.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime


def render_capa_panel(capa_data: Optional[Dict[str, Any]] = None):
    """
    Render CAPA Recommendations panel (CHUNK 6.15).
    
    Args:
        capa_data: Dictionary containing CAPA recommendations data
    """
    if capa_data is None:
        # Try to get from session state
        capa_data = st.session_state.get("capa_recommendations")
    
    if not capa_data:
        st.info("🛠️ **No CAPA recommendations available.**")
        st.markdown("""
        To generate CAPA recommendations:
        
        1. **Via Chat:** Type "What CAPA actions should we take?" or "Regulatory next steps?"
        2. **Via Button:** Click "🛠️ Generate CAPA" in the Trend Alerts tab
        3. **Via Query:** Ask "How do we mitigate this risk?" or "What do we need to prepare?"
        
        The CAPA recommendations will include:
        - Root cause hypothesis
        - Corrective actions (immediate)
        - Preventive actions (long-term)
        - Required regulatory notifications
        - Risk minimization measures (RMM)
        - Impact on benefit-risk
        - Recommended timeline (1-30-90 days)
        - Inspection readiness preparation
        """)
        return
    
    # Extract CAPA content
    content = capa_data.get("content", "")
    meta = capa_data.get("meta", {})
    generated_on = capa_data.get("generated_on", datetime.now().isoformat())
    
    if not content:
        st.warning("CAPA recommendations content is empty. Please regenerate.")
        return
    
    # Header
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.subheader("🛠️ CAPA Recommendations")
    st.caption("Corrective and Preventive Actions for Identified Safety Signals")
    
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
    
    # Priority indicator
    priority_signals = capa_data.get("priority_signals", [])
    if priority_signals:
        st.info(f"⚠️ **{len(priority_signals)} high-priority signals** identified requiring immediate attention.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # CAPA Content
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    
    # Render markdown content
    st.markdown(content)
    
    # Action items summary (if available in payload)
    payload = capa_data.get("payload", {})
    if payload:
        rpf_ranked = payload.get("rpf_ranked", [])
        if rpf_ranked:
            st.markdown("---")
            st.markdown("### 📊 Associated Priority Signals")
            for idx, entry in enumerate(rpf_ranked[:5], 1):
                signal = entry.get("signal", {})
                rpf_score = entry.get("rpf_score", 0)
                risk_level = entry.get("risk_level", "Unknown")
                drug_sig = signal.get("drug", "Unknown")
                reaction_sig = signal.get("reaction", "Unknown")
                
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{idx}. {drug_sig} → {reaction_sig}**")
                with col_b:
                    st.write(f"{risk_level} (Score: {rpf_score:.1f})")
    
    # Download button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("💡 These CAPA recommendations are AI-generated based on identified signals and risks. Review and validate before implementation.")
    with col2:
        # Create downloadable text file
        capa_text = f"""
CAPA RECOMMENDATIONS
Generated: {generated_on}
Drug: {drug}
Reaction: {reaction}

{content}
        """
        file_name = f"CAPA_{drug}_{reaction}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="📥 Download CAPA",
            data=capa_text,
            file_name=file_name,
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

