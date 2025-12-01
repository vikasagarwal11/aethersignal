"""
Global Theme System - Consistent styling across the platform
"""

import streamlit as st
from typing import Dict


# Color palettes
LIGHT_THEME: Dict[str, str] = {
    "bg": "#F8F9FB",
    "sidebar_bg": "#FFFFFF",
    "card_bg": "#FFFFFF",
    "text": "#1A1A1A",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary": "#64748B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#06B6D4",
    "border": "#E2E8F0",
    "border_light": "#F1F5F9",
    "shadow": "rgba(0, 0, 0, 0.05)",
    "shadow_hover": "rgba(0, 0, 0, 0.1)",
}

DARK_THEME: Dict[str, str] = {
    "bg": "#0F172A",
    "sidebar_bg": "#1E293B",
    "card_bg": "#1E293B",
    "text": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "secondary": "#94A3B8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#06B6D4",
    "border": "#334155",
    "border_light": "#1E293B",
    "shadow": "rgba(0, 0, 0, 0.3)",
    "shadow_hover": "rgba(0, 0, 0, 0.5)",
}


def get_theme_colors() -> Dict[str, str]:
    """
    Get current theme colors.
    
    Returns:
        Dictionary of color values
    """
    mode = st.session_state.get("theme_mode", "light")
    return LIGHT_THEME if mode == "light" else DARK_THEME


def apply_global_theme():
    """
    Apply global theme CSS to Streamlit.
    """
    colors = get_theme_colors()
    
    st.markdown(f"""
    <style>
    /* Global Theme Variables */
    :root {{
        --bg: {colors['bg']};
        --sidebar-bg: {colors['sidebar_bg']};
        --card-bg: {colors['card_bg']};
        --text: {colors['text']};
        --text-secondary: {colors['text_secondary']};
        --text-muted: {colors['text_muted']};
        --primary: {colors['primary']};
        --primary-hover: {colors['primary_hover']};
        --secondary: {colors['secondary']};
        --success: {colors['success']};
        --warning: {colors['warning']};
        --error: {colors['error']};
        --info: {colors['info']};
        --border: {colors['border']};
        --border-light: {colors['border_light']};
        --shadow: {colors['shadow']};
        --shadow-hover: {colors['shadow_hover']};
    }}
    
    /* Main Container */
    .main {{
        background-color: var(--bg);
        padding: 2rem;
    }}
    
    /* Headers */
    h1 {{
        color: var(--text);
        font-weight: 700;
        margin-bottom: 1rem;
        font-size: 2rem;
    }}
    
    h2 {{
        color: var(--text);
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }}
    
    h3 {{
        color: var(--text);
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        font-size: 1.25rem;
    }}
    
    /* Cards */
    .aether-card {{
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 6px var(--shadow);
        margin-bottom: 1rem;
        border: 1px solid var(--border-light);
        transition: all 0.2s ease;
    }}
    
    .aether-card:hover {{
        box-shadow: 0 4px 12px var(--shadow-hover);
        transform: translateY(-2px);
    }}
    
    /* Buttons */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: none;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 6px var(--shadow-hover);
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg);
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
    }}
    
    [data-testid="stMetricLabel"] {{
        color: var(--text-secondary);
        font-size: 0.875rem;
    }}
    
    /* Tables */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-light);
    }}
    
    /* Loading Spinner */
    .stSpinner > div {{
        border-color: var(--primary);
    }}
    
    /* Breadcrumbs */
    .breadcrumb {{
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-bottom: 1rem;
    }}
    
    .breadcrumb a {{
        color: var(--primary);
        text-decoration: none;
    }}
    
    .breadcrumb a:hover {{
        text-decoration: underline;
    }}
    </style>
    """, unsafe_allow_html=True)

