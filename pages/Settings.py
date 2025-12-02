"""
Settings Page - Global settings and configuration
"""

import streamlit as st
from src.settings.settings_page import render_settings_page

st.set_page_config(
    page_title="AetherSignal — Settings",
    page_icon="⚙️",
    layout="wide"
)

render_settings_page()

