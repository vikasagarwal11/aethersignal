"""
API Keys Page - API key management
"""

import streamlit as st
from src.settings.api_key_manager import render_api_key_manager

st.set_page_config(
    page_title="AetherSignal — API Keys",
    page_icon="🔐",
    layout="wide"
)

render_api_key_manager()

