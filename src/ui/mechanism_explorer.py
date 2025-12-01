"""
Mechanism Explorer UI (Phase 3D.5)
Interactive panel for exploring drug mechanisms and biological pathways.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import logging

from src.mechanism.mechanistic_chain_generator import MechanisticChainGenerator
from src.mechanism.llm_mechanistic_reasoner import LLMMechanisticReasoner
from src.mechanism.mechanistic_plausibility_scorer import MechanisticPlausibilityScorer

logger = logging.getLogger(__name__)


def render_mechanism_explorer(
    drug: Optional[str] = None,
    reaction: Optional[str] = None
):
    """
    Render mechanism explorer panel.
    
    Args:
        drug: Optional drug name
        reaction: Optional reaction name
    """
    st.header("🧠 Mechanism Explorer")
    st.caption("Biological pathway reasoning and mechanistic explanations")
    
    # Initialize engines
    chain_generator = MechanisticChainGenerator()
    llm_reasoner = LLMMechanisticReasoner()
    plausibility_scorer = MechanisticPlausibilityScorer()
    
    # Drug and reaction inputs
    col1, col2 = st.columns(2)
    with col1:
        drug_input = st.text_input("Drug", value=drug or "Semaglutide")
    with col2:
        reaction_input = st.text_input("Reaction", value=reaction or "Nausea")
    
    if st.button("🔬 Analyze Mechanism", type="primary"):
        with st.spinner("Generating mechanistic chain..."):
            # Generate chain
            chain_result = chain_generator.generate_chain(drug_input, reaction_input)
            
            # Calculate plausibility
            plausibility_result = plausibility_scorer.calculate_score(
                drug_input,
                reaction_input,
                pathway_evidence=0.7 if chain_result.get("pathways") else 0.3,
                similar_drug_support=0.6
            )
            
            # Generate LLM explanation
            llm_result = llm_reasoner.explain_mechanism(
                drug_input,
                reaction_input,
                chain_result.get("chain", []),
                chain_result.get("targets", []),
                chain_result.get("pathways", []),
                literature_support=0.7
            )
            
            # Store in session state
            st.session_state["mechanism_result"] = {
                "chain": chain_result,
                "plausibility": plausibility_result,
                "explanation": llm_result
            }
    
    # Display results
    if "mechanism_result" in st.session_state:
        result = st.session_state["mechanism_result"]
        
        # Plausibility score
        st.markdown("### Plausibility Score")
        plausibility = result["plausibility"]["plausibility_score"]
        category = result["plausibility"]["category"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Plausibility Score", f"{plausibility:.2f}")
        with col2:
            st.metric("Category", category.replace("_", " ").title())
        with col3:
            st.metric("Confidence", result["explanation"].get("confidence", "moderate").title())
        
        # Mechanism chain
        st.markdown("### Mechanism Chain")
        chain = result["chain"].get("chain", [])
        if chain:
            for i, step in enumerate(chain, 1):
                st.write(f"{i}. {step}")
        else:
            st.info("No mechanistic chain found")
        
        # LLM explanation
        st.markdown("### AI Explanation")
        explanation = result["explanation"].get("explanation", "")
        st.write(explanation)
        
        # Component breakdown
        st.markdown("### Plausibility Components")
        components = result["plausibility"]["components"]
        comp_df = pd.DataFrame([
            {"Component": k.replace("_", " ").title(), "Score": v}
            for k, v in components.items()
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        
        # Pathway IDs
        pathway_ids = result["chain"].get("pathway_ids", [])
        if pathway_ids:
            st.markdown("### Pathway IDs")
            st.write(", ".join(pathway_ids))
        
        # Mechanism graph visualization
        st.markdown("### Mechanism Graph")
        render_mechanism_graph(result["chain"])


def render_mechanism_graph(chain_result: Dict[str, Any]):
    """Render mechanism graph visualization."""
    chain = chain_result.get("chain", [])
    if not chain:
        st.info("No mechanism chain to visualize")
        return
    
    # Create simple graph visualization
    # In production, would use networkx + plotly for interactive graph
    st.info("📊 Interactive mechanism graph visualization coming soon")
    
    # For now, show chain as text
    st.write("**Mechanistic Pathway:**")
    for i, step in enumerate(chain, 1):
        st.write(f"Step {i}: {step}")

