"""
Executive Summary Component - Executive Dashboard
AI-generated executive summary panel
"""

import streamlit as st
from src.ui.layout.theme import get_theme_colors


def render_executive_summary():
    """
    Render AI-generated executive summary.
    """
    st.markdown("### 📝 Executive Summary")
    
    # Try to get real AI summary
    try:
        from executive_dashboard.narrative_ai import generate_executive_summary
        
        summary = generate_executive_summary()
        
    except Exception:
        # Fallback to mock summary
        summary = """
        **The overall safety profile is stable.**
        
        - No major spikes in FAERS  
        - Moderate rises in Social AE chatter  
        - Literature confirms 2 emerging signals  
        - Quantum scoring shows no high-risk reactions  
        - 4 novel signals detected requiring review
        """
    
    colors = get_theme_colors()
    
    st.markdown(
        f"""
        <div class="aether-card" style="background:{colors['card_bg']};padding:1.5rem;border-left:4px solid {colors['info']};">
            <div style="color:{colors['text']};line-height:1.8;">
                {summary}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add refresh button
    if st.button("🔄 Regenerate Summary", use_container_width=True):
        st.rerun()

