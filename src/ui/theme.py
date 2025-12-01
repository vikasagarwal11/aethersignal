"""
Global Theme & Styling - Consistent design system
"""

import streamlit as st


def apply_theme():
    """
    Apply global theme styling to Streamlit.
    """
    st.markdown("""
    <style>
    /* Global Styles */
    .main {
        padding: 2rem;
    }
    
    /* Headers */
    h1 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #374151;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #4b5563;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Tables */
    .dataframe {
        border-radius: 6px;
        overflow: hidden;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f9fafb;
    }
    
    /* Loading */
    .stSpinner > div {
        border-color: #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)


def get_color_palette() -> Dict[str, str]:
    """
    Get the color palette.
    
    Returns:
        Dictionary of color names to hex values
    """
    return {
        "primary": "#3b82f6",
        "secondary": "#8b5cf6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#06b6d4",
        "background": "#ffffff",
        "surface": "#f9fafb",
        "text": "#1f2937",
        "text_secondary": "#6b7280"
    }

