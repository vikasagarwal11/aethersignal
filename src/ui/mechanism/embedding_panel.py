"""
Embedding Panel - Embedding visualization
"""

import streamlit as st
from typing import Dict, Any
from .components import similarity_heatmap
import plotly.express as px
import pandas as pd


def embedding_panel(fusion_result: Dict[str, Any]):
    """
    Render embedding similarity panel.
    
    Args:
        fusion_result: Fusion result dictionary
    """
    st.subheader("🔢 Embedding Similarity Scores")
    
    # Extract similarity scores
    drug_reaction_sim = fusion_result.get("drug_reaction_similarity", 0.0)
    mechanism_reaction_sim = fusion_result.get("mechanism_reaction_similarity", 0.0)
    fusion_score = fusion_result.get("fusion_score", 0.0)
    
    # Create similarity data
    similarities = [
        {"metric": "Drug-Reaction", "score": drug_reaction_sim},
        {"metric": "Mechanism-Reaction", "score": mechanism_reaction_sim},
        {"metric": "Fusion Score", "score": fusion_score}
    ]
    
    # Bar chart
    df = pd.DataFrame(similarities)
    fig = px.bar(
        df,
        x="metric",
        y="score",
        color="score",
        color_continuous_scale="Viridis",
        title="Embedding Similarity Scores",
        labels={"score": "Similarity Score", "metric": "Metric"}
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Drug-Reaction", f"{drug_reaction_sim:.3f}")
    col2.metric("Mechanism-Reaction", f"{mechanism_reaction_sim:.3f}")
    col3.metric("Fusion Score", f"{fusion_score:.3f}")
    
    # Detailed view
    with st.expander("Detailed Fusion Results"):
        st.json(fusion_result)

