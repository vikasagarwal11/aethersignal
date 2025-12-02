"""
Pathway Graph Section - Renders graph + pathway list
"""

import streamlit as st
from typing import Dict, List, Any
from .knowledge_graph_viewer import render_kg
from .components import pathway_list


def pathway_graph_section(graph: Dict[str, Any], pathways: List[Dict[str, Any]]):
    """
    Render pathway graph section.
    
    Args:
        graph: Graph dictionary
        pathways: List of pathway dictionaries
    """
    st.subheader("🧬 Mechanistic Pathway Graph")
    
    # Layout selector
    layout = st.selectbox(
        "Graph Layout",
        ["spring", "circular", "hierarchical"],
        key="kg_layout"
    )
    
    render_kg(graph, layout=layout)
    
    st.markdown("---")
    st.subheader("📚 Related Pathways")
    pathway_list(pathways)
    
    # Pathway statistics
    if pathways:
        with st.expander("Pathway Statistics"):
            avg_distance = sum(p.get("distance", 0.0) for p in pathways) / len(pathways)
            st.metric("Average Distance", f"{avg_distance:.4f}")
            st.metric("Total Pathways", len(pathways))

