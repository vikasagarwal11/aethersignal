"""
Mechanistic Fusion Tiles - KPI tiles for executive dashboard
"""

import streamlit as st
from typing import Union


def mech_tile(label: str, value: Union[str, int, float], color: str = "#2563eb"):
    """
    Render a mechanistic KPI tile.
    
    Args:
        label: Tile label
        value: Tile value (will be converted to string)
        color: Color theme
    """
    value_str = str(value) if not isinstance(value, str) else value
    
    st.markdown(f"""
    <div style="
        padding: 18px;
        background: {color}15;
        border-left: 5px solid {color};
        border-radius: 10px;
        margin-bottom: 10px;
    ">
        <h4 style="margin:0;color:{color}">{label}</h4>
        <h2 style="margin:0;font-weight:700">{value_str}</h2>
    </div>
    """, unsafe_allow_html=True)

