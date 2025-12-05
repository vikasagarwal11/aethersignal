"""
AetherSignal – Admin Data Source Control Center
Super Admin panel for managing all data sources.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.auth.auth import is_authenticated
from src.ui.admin_data_sources_panel import render_admin_data_sources_panel
from src.data_sources import DataSourceManager

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AetherSignal – Admin Data Sources",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()

# -------------------------------------------------------------------
# TOP NAVIGATION - MUST BE FIRST st.* CALL AFTER apply_theme()
# -------------------------------------------------------------------
render_top_nav()

# -------------------------------------------------------------------
# AUTHENTICATION CHECK
# -------------------------------------------------------------------
# TODO: Add proper admin role check
# For now, allow access (add role-based access control later)
if not is_authenticated():
    st.warning("⚠️ Please log in to access the Admin Panel")
    if st.button("Go to Login"):
        st.switch_page("pages/Login.py")
    st.stop()

# -------------------------------------------------------------------
# ADMIN DATA SOURCE CONTROL CENTER
# -------------------------------------------------------------------

# Initialize DataSourceManager
if 'data_source_manager' not in st.session_state:
    st.session_state.data_source_manager = DataSourceManager()

manager = st.session_state.data_source_manager

# Render admin panel
render_admin_data_sources_panel(manager)

