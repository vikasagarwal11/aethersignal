"""
Label Intelligence UI - Compare FDA labels vs real-world evidence
"""

import streamlit as st
from src.ui.layout.base_layout import render_base_layout


def render_label_intelligence():
    """
    Render the Label Intelligence interface.
    """
    def page_content():
        st.title("📑 Label Intelligence")
        st.caption("Compare FDA-approved labels vs FAERS vs Social vs Literature")
        
        st.info(
            """
            **Label Intelligence** will show:
            
            - FDA label reactions (from DailyMed)
            - FAERS-reported reactions
            - Social media mentions
            - Literature case reports
            - **Label gaps** (reactions not in label but reported elsewhere)
            """
        )
        
        # Placeholder for future implementation
        drug = st.text_input("Drug Name", placeholder="e.g., Semaglutide")
        
        if drug:
            st.button("📑 Analyze Label Gaps", type="primary", use_container_width=True)
            st.info("Label gap analysis will be available in Wave 2+")
    
    render_base_layout(page_content)

