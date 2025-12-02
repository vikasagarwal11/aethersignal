"""
Mechanistic Signal Card - Individual signal card for executive dashboard
"""

import streamlit as st
from typing import Dict, Any


def mechanistic_signal_card(entry: Dict[str, Any]):
    """
    Render a mechanistic signal card.
    
    Args:
        entry: Signal entry dictionary with analysis results
    """
    drug = entry.get("drug", "Unknown")
    reaction = entry.get("reaction", "Unknown")
    
    # Get evidence score
    evidence_score = entry.get("evidence_score", {})
    if isinstance(evidence_score, dict):
        score = round(evidence_score.get("score", evidence_score.get("evidence_score", 0.0)), 3)
    else:
        score = round(float(evidence_score), 3)
    
    # Get alert status
    alert = entry.get("alert", {})
    if isinstance(alert, dict):
        alert_status = alert.get("alert", False)
    else:
        alert_status = bool(alert)
    
    # Get fusion and causal scores
    fusion_score = entry.get("fusion", {}).get("fusion_score", 0.0) if isinstance(entry.get("fusion"), dict) else 0.0
    causal_score = entry.get("causal", {}).get("causal_score", 0.0) if isinstance(entry.get("causal"), dict) else 0.0
    is_novel = entry.get("novel", False)
    
    color = "#dc2626" if alert_status else "#2563eb"
    
    st.markdown(f"""
        <div style="
            padding: 14px;
            border-radius: 12px;
            border: 1px solid {color}60;
            background: {color}15;
            margin-bottom: 12px;
        ">
            <h3 style="margin: 0; color: {color};">
                {drug} → {reaction}
            </h3>
            <p style="margin: 4px 0;">
                Evidence Score: <strong>{score}</strong>
            </p>
            <p style="margin: 4px 0; font-size: 0.9em; color: #6b7280;">
                Fusion: {round(fusion_score, 3)} | 
                Causal: {round(causal_score, 3)} | 
                Novel: {"Yes" if is_novel else "No"}
            </p>
        </div>
    """, unsafe_allow_html=True)

