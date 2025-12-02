"""
Mechanistic Alert Panel - Alert visualization
"""

import streamlit as st
from typing import Dict, Any


def mechanistic_alert_panel(alert_info: Dict[str, Any]):
    """
    Render mechanistic alert panel.
    
    Args:
        alert_info: Alert information dictionary
    """
    alert = alert_info.get("alert", False)
    score = alert_info.get("alert_score", 0.0)
    fusion = alert_info.get("fusion", 0.0)
    causal = alert_info.get("causal", 0.0)
    is_novel = alert_info.get("is_novel", False)
    
    color = "#dc2626" if alert else "#16a34a"
    label = "⚠️ HIGH-RISK MECHANISTIC ALERT" if alert else "✅ NO ALERT"
    icon = "⚠️" if alert else "✅"
    
    st.markdown(f"""
        <div style="
            padding: 16px;
            border-radius: 10px;
            background: {color}20;
            border-left: 5px solid {color};
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; color: {color};">
                {icon} {label}
            </h3>
            <p style="margin: 6px 0 0 0;">
                Alert Score: <strong>{round(score, 3)}</strong>
            </p>
            <div style="margin-top: 10px; font-size: 0.9em; color: #6b7280;">
                <div>Fusion: {round(fusion, 3)} | Causal: {round(causal, 3)} | Novel: {'Yes' if is_novel else 'No'}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Additional details in expander
    with st.expander("Alert Details"):
        st.json(alert_info)

