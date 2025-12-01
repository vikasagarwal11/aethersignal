"""
Enterprise Heatmap Renderer (CHUNK A4)
Polished enterprise-grade heatmap visualization with color-coding.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Optional


def _apply_enterprise_colors(value: Any) -> tuple:
    """
    Apply enterprise color scheme to a single value.
    
    Args:
        value: Risk level string or numeric value
        
    Returns:
        Tuple of (background_color, text_color)
    """
    # Handle string risk levels
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ["high", "critical"]:
            return ("#FDE7E9", "#A4262C")  # Red zone
        elif value_lower == "medium":
            return ("#FFF4CE", "#8A6D00")  # Yellow zone
        elif value_lower == "low":
            return ("#E6F4EA", "#0B6B33")  # Green zone
        else:
            return ("#FFFFFF", "#000000")  # N/A - white
    
    # Handle numeric values (0-100 scale)
    if isinstance(value, (int, float)):
        if value >= 85:
            return ("#E6F4EA", "#0B6B33")  # Green zone
        elif value >= 60:
            return ("#FFF4CE", "#8A6D00")  # Yellow zone
        else:
            return ("#FDE7E9", "#A4262C")  # Red zone
    
    return ("#FFFFFF", "#000000")  # Default


def render_enterprise_heatmap(df: pd.DataFrame, title: str = "Governance Heatmap") -> None:
    """
    Render enterprise-styled heatmap DataFrame.
    
    Args:
        df: DataFrame with risk/compliance levels
        title: Title for the heatmap
    """
    st.markdown(f"### {title}")
    
    if df is None or df.empty:
        st.info("No data available for heatmap visualization.")
        return
    
    # Create styled DataFrame
    styled_df = df.style.applymap(
        lambda x: "background-color: {}; color: {}".format(*_apply_enterprise_colors(x))
    ).set_table_styles([
        {
            'selector': 'th',
            'props': [('background-color', '#E3ECF9'), ('color', '#003A75'), ('font-weight', 'bold')]
        },
        {
            'selector': 'td',
            'props': [('text-align', 'center'), ('padding', '8px')]
        }
    ])
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Legend
    st.markdown("---")
    st.markdown("#### 📊 Color Legend")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div style="background-color: #E6F4EA; color: #0B6B33; padding: 8px; border-radius: 4px; text-align: center; font-weight: bold;">🟢 Low Risk</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div style="background-color: #FFF4CE; color: #8A6D00; padding: 8px; border-radius: 4px; text-align: center; font-weight: bold;">🟡 Medium Risk</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div style="background-color: #FDE7E9; color: #A4262C; padding: 8px; border-radius: 4px; text-align: center; font-weight: bold;">🔴 High Risk</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div style="background-color: #FFFFFF; color: #000000; padding: 8px; border-radius: 4px; text-align: center; font-weight: bold;">⚪ N/A</div>', unsafe_allow_html=True)

