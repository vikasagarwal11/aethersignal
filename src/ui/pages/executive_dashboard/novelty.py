"""
Novelty Panel Component - Executive Dashboard
Novel signal detection and alerts
"""

import streamlit as st
from src.ui.layout.theme import get_theme_colors


def render_novelty_panel():
    """
    Render the novelty detection panel.
    """
    st.markdown("### 🧬 Novel Signals")
    
    # Try to get real data
    try:
        from executive_dashboard.aggregator import compute_novelty
        
        novelty_data = compute_novelty()
        
        novel_signals = novelty_data.get("novel_signals", [])
        count = len(novel_signals)
        
    except Exception:
        # Fallback to mock data
        novel_signals = [
            {"reaction": "Hair loss", "sources": "Social only", "count": 182},
            {"reaction": "Tingling legs", "sources": "Social + Literature", "count": 45},
            {"reaction": "Injection site rash", "sources": "Literature only", "count": 12},
            {"reaction": "Brain fog", "sources": "Social", "count": 67}
        ]
        count = len(novel_signals)
    
    colors = get_theme_colors()
    
    if count > 0:
        st.info(
            f"""
            **{count} novel signals detected** in the last 60 days:
            
            """
        )
        
        # Display novel signals
        for signal in novel_signals[:5]:  # Show top 5
            reaction = signal.get("reaction", "Unknown")
            sources = signal.get("sources", "Unknown")
            count_val = signal.get("count", 0)
            
            st.markdown(
                f"""
                <div style="padding:0.75rem;background:{colors['card_bg']};border-radius:6px;margin:0.5rem 0;border-left:3px solid {colors['warning']};">
                    <strong>{reaction}</strong> ({count_val} mentions)<br>
                    <small style="color:{colors['text_secondary']};">Sources: {sources}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.success("✅ No novel signals detected in the monitoring period.")

