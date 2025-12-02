"""
Mechanistic Ranking Table - Evidence ranking visualization
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def mech_ranking_table(entries: List[Dict[str, Any]]):
    """
    Render mechanistic evidence ranking table.
    
    Args:
        entries: List of mechanistic analysis entries
    """
    if not entries:
        st.warning("No entries available for ranking.")
        return
    
    try:
        rows = []
        for e in entries:
            drug = e.get("drug", "Unknown")
            reaction = e.get("reaction", "Unknown")
            
            # Get evidence score
            evidence = e.get("evidence_score", {})
            if isinstance(evidence, dict):
                evidence_score = evidence.get("score", evidence.get("evidence_score", 0.0))
            else:
                evidence_score = float(evidence)
            
            # Get fusion score
            fusion = e.get("fusion", {})
            fusion_score = fusion.get("fusion_score", 0.0) if isinstance(fusion, dict) else 0.0
            
            # Get causal score
            causal = e.get("causal", {})
            causal_score = causal.get("causal_score", 0.0) if isinstance(causal, dict) else 0.0
            
            is_novel = e.get("novel", False)
            
            rows.append({
                "Drug": drug,
                "Reaction": reaction,
                "Evidence Score": round(evidence_score, 3),
                "Fusion": round(fusion_score, 3),
                "Causal": round(causal_score, 3),
                "Novel": "Yes" if is_novel else "No",
                "Alert": "⚠️" if e.get("alert", {}).get("alert", False) else "✅"
            })
        
        df = pd.DataFrame(rows)
        
        if df.empty:
            st.warning("No data available for ranking table.")
            return
        
        # Sort by evidence score
        df = df.sort_values("Evidence Score", ascending=False)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Summary statistics
        with st.expander("Summary Statistics"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Signals", len(df))
            col2.metric("Avg Evidence Score", f"{df['Evidence Score'].mean():.3f}")
            col3.metric("Novel Signals", len(df[df["Novel"] == "Yes"]))
        
    except Exception as e:
        logger.error(f"Ranking table error: {e}")
        st.error(f"Error rendering ranking table: {e}")

