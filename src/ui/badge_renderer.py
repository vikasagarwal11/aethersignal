"""
Badge Renderer (CHUNK A5.2)
Professional, compact, color-coded badges for lifecycle, severity, and trend indicators.
"""
import streamlit as st
from typing import Optional

try:
    from src.styles import BADGE_STYLES
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False
    BADGE_STYLES = {}


def render_badge(label: str, category: str = "lifecycle", key: Optional[str] = None) -> None:
    """
    Render a color-coded badge.
    
    Args:
        label: Badge label text
        category: Badge category ("lifecycle", "severity", "trend")
        key: Optional unique key for Streamlit widget
    """
    if not STYLES_AVAILABLE:
        # Fallback: plain text
        st.markdown(f"**{label}**")
        return
    
    color = BADGE_STYLES.get(category, {}).get(label, "#6B7280")
    
    # Use inline HTML for badge styling
    st.markdown(
        f"""
        <span style="
            padding: 4px 10px;
            background-color: {color};
            color: white;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 6px;
            display: inline-block;
            white-space: nowrap;
        ">
        {label}
        </span>
        """,
        unsafe_allow_html=True
    )


def render_badge_row(labels: list, categories: list = None) -> None:
    """
    Render multiple badges in a row.
    
    Args:
        labels: List of badge labels
        categories: List of categories (defaults to "lifecycle" for all)
    """
    if categories is None:
        categories = ["lifecycle"] * len(labels)
    
    badges_html = ""
    for label, category in zip(labels, categories):
        if not STYLES_AVAILABLE:
            badges_html += f"<strong>{label}</strong> "
            continue
        
        color = BADGE_STYLES.get(category, {}).get(label, "#6B7280")
        badges_html += f"""
        <span style="
            padding: 4px 10px;
            background-color: {color};
            color: white;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 6px;
            display: inline-block;
            white-space: nowrap;
        ">
        {label}
        </span>
        """
    
    st.markdown(badges_html, unsafe_allow_html=True)

