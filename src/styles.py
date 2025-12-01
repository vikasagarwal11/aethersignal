"""
Enterprise Style Definitions (CHUNK A5.1)
Badge styles and color schemes for governance visualization.
"""
import streamlit as st

def apply_theme():
    """
    Apply centralized theme stylesheet to Streamlit app.
    This function applies the enterprise theme CSS across all pages.
    """
    st.markdown("""
    <style>
    /* Enterprise Theme Styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Add any additional theme styles here */
    </style>
    """, unsafe_allow_html=True)

BADGE_STYLES = {
    "lifecycle": {
        "Triage": "#6B7280",
        "Validation": "#2563EB",
        "Assessment": "#1D4ED8",
        "Evaluation": "#0EA5E9",
        "Recommendation": "#F59E0B",
        "CAPA": "#DC2626",
        "Closed": "#059669",
        "Under Assessment": "#1D4ED8",
        "Signal Evaluation": "#0EA5E9",
        "Corrective/Preventive Action (CAPA)": "#DC2626"
    },
    "severity": {
        "low": "#10B981",
        "medium": "#FBBF24",
        "high": "#EF4444",
        "Low": "#10B981",
        "Medium": "#FBBF24",
        "High": "#EF4444",
        "Critical": "#DC2626"
    },
    "trend": {
        "stable": "#2563EB",
        "increasing": "#F59E0B",
        "spiking": "#EF4444",
        "Low": "#2563EB",
        "Medium": "#F59E0B",
        "High": "#EF4444",
        "N/A": "#6B7280"
    }
}
