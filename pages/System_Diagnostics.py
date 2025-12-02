"""
System Diagnostics Page - System health and diagnostics
"""

import streamlit as st
from src.system.diagnostics import render_diagnostics_dashboard

st.set_page_config(
    page_title="AetherSignal — System Diagnostics",
    page_icon="🔍",
    layout="wide"
)

render_diagnostics_dashboard()

