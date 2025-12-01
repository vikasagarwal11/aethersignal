"""
Evidence Grid - Unified evidence display from all sources
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.ui.layout.theme import get_theme_colors


def render_evidence_grid(evidence: Dict[str, Any]):
    """
    Render unified evidence grid.
    
    Args:
        evidence: Unified evidence dictionary
    """
    st.subheader("🧩 Unified Evidence")
    
    if not evidence:
        st.warning("No evidence data available")
        return
    
    colors = get_theme_colors()
    
    # Prepare evidence data
    evidence_rows = []
    
    sources = {
        "FAERS": evidence.get("faers", {}),
        "Social": evidence.get("social", {}),
        "Literature": evidence.get("literature", {}),
        "Mechanism": evidence.get("mechanism", {}),
        "Causality": evidence.get("causality", {}),
        "Label": evidence.get("label", {})
    }
    
    for source_name, source_data in sources.items():
        if source_data:
            # Format evidence summary
            if isinstance(source_data, dict):
                summary = source_data.get("summary", str(source_data))
            else:
                summary = str(source_data)
            
            evidence_rows.append({
                "Source": source_name,
                "Evidence": summary[:200] + "..." if len(str(summary)) > 200 else summary,
                "Available": "✅"
            })
        else:
            evidence_rows.append({
                "Source": source_name,
                "Evidence": "No data",
                "Available": "❌"
            })
    
    # Display as dataframe
    df = pd.DataFrame(evidence_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show consensus score if available
    if "consensus_score" in evidence:
        consensus = evidence["consensus_score"]
        st.metric("Consensus Score", f"{consensus:.2f}")
    
    # Show evidence strength
    if "evidence_strength" in evidence:
        strength = evidence["evidence_strength"]
        strength_colors = {
            "STRONG": colors["success"],
            "MODERATE": colors["warning"],
            "WEAK": colors["error"],
            "INSUFFICIENT": colors["text_muted"]
        }
        color = strength_colors.get(strength, colors["text"])
        
        st.markdown(
            f'<div style="padding:0.75rem;background:{colors["card_bg"]};border-radius:6px;border-left:4px solid {color};">'
            f'<strong>Evidence Strength:</strong> {strength}'
            f'</div>',
            unsafe_allow_html=True
        )

