"""
Mechanism Explorer UI - Drug → Target → Pathway → AE visualization
"""

import streamlit as st
from src.ui.layout.base_layout import render_base_layout
from src.ui.layout.state import GlobalState


def render_mechanism_explorer():
    """
    Render the Mechanism Explorer interface.
    """
    def page_content():
        st.title("🧬 Mechanism Explorer")
        st.caption("Explore biological pathways connecting drugs to adverse events")
        
        st.info(
            """
            **Mechanism reasoning engine** will visualize drug → target → pathway → AE relationships.
            
            This feature helps understand the biological plausibility of drug-AE associations.
            """
        )
        
        # Placeholder for future implementation
        col1, col2 = st.columns(2)
        
        with col1:
            drug = st.text_input("Drug Name", placeholder="e.g., Semaglutide")
        
        with col2:
            ae = st.text_input("Adverse Event", placeholder="e.g., Nausea")
        
        if drug and ae:
            st.button("🔬 Analyze Mechanism", type="primary", use_container_width=True)
            st.info("Mechanism analysis will be available in Wave 2+")
    
    render_base_layout(page_content)

