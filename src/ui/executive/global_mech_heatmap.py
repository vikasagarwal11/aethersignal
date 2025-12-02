"""
Global Mechanistic Heatmap - Cross-drug evidence visualization
"""

import plotly.express as px
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def global_mech_heatmap(entries: List[Dict[str, Any]]):
    """
    Render global mechanistic evidence heatmap.
    
    Args:
        entries: List of mechanistic analysis entries
    """
    if not entries:
        st.warning("No mechanistic entries available.")
        return
    
    try:
        # Extract data
        rows = []
        for e in entries:
            drug = e.get("drug", "Unknown")
            reaction = e.get("reaction", "Unknown")
            
            # Get fusion score
            fusion = e.get("fusion", {})
            fusion_score = fusion.get("fusion_score", 0.0) if isinstance(fusion, dict) else 0.0
            
            # Get causal score
            causal = e.get("causal", {})
            causal_score = causal.get("causal_score", 0.0) if isinstance(causal, dict) else 0.0
            
            # Get evidence score
            evidence = e.get("evidence_score", {})
            if isinstance(evidence, dict):
                evidence_score = evidence.get("score", evidence.get("evidence_score", 0.0))
            else:
                evidence_score = float(evidence)
            
            rows.append({
                "drug": drug,
                "reaction": reaction,
                "fusion": fusion_score,
                "causal": causal_score,
                "evidence": evidence_score
            })
        
        df = pd.DataFrame(rows)
        
        if df.empty:
            st.warning("No data available for heatmap.")
            return
        
        # Create pivot table
        pivot = df.pivot_table(
            values="evidence",
            index="drug",
            columns="reaction",
            aggfunc="mean",
            fill_value=0.0
        )
        
        if pivot.empty:
            st.warning("Insufficient data for heatmap visualization.")
            return
        
        # Create heatmap
        fig = px.imshow(
            pivot,
            color_continuous_scale="RdBu",
            aspect="auto",
            labels=dict(
                x="Reaction",
                y="Drug",
                color="Evidence Score"
            ),
            title="Global Mechanistic Evidence Heatmap"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Heatmap rendering error: {e}")
        st.error(f"Error rendering heatmap: {e}")

