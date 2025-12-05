"""
Navigation Components - Global sidebar, breadcrumbs, page routing
"""

import streamlit as st
from typing import List, Dict, Optional
import os


# Page configuration
PAGES = {
    "🏠 Home": {
        "path": "Home",
        "icon": "🏠",
        "category": "Main"
    },
    "🔍 Quantum PV Explorer": {
        "path": "1_Quantum_PV_Explorer",
        "icon": "🔍",
        "category": "Main"
    },
    "📊 AE Explorer": {
        "path": "3_AE_Explorer",
        "icon": "📊",
        "category": "Main"
    },
    "🌐 Social AE Explorer": {
        "path": "2_Social_AE_Explorer",
        "icon": "🌐",
        "category": "Data Sources"
    },
    "📈 Executive Dashboard": {
        "path": "99_Executive_Dashboard",
        "icon": "📈",
        "category": "Dashboards"
    },
    "🧠 Safety Copilot": {
        "path": "4_Safety_Copilot",
        "icon": "🧠",
        "category": "AI Tools"
    },
    "🔬 Mechanism Explorer": {
        "path": "5_Mechanism_Explorer",
        "icon": "🔬",
        "category": "AI Tools"
    },
    "⚠️ Risk Dashboard": {
        "path": "6_Risk_Dashboard",
        "icon": "⚠️",
        "category": "Dashboards"
    },
    "📋 Workflow Dashboard": {
        "path": "7_Workflow_Dashboard",
        "icon": "📋",
        "category": "Workflows"
    },
    "📄 Report Builder": {
        "path": "8_Report_Builder",
        "icon": "📄",
        "category": "Reports"
    },
    "🔐 Data Source Manager": {
        "path": "98_🔐_Data_Source_Manager",
        "icon": "🔐",
        "category": "Admin"
    },
    "🛡️ Evidence Governance": {
        "path": "100_Evidence_Governance",
        "icon": "🛡️",
        "category": "Admin"
    }
}


def get_active_page() -> Optional[str]:
    """
    Get the currently active page.
    
    Returns:
        Page path or None
    """
    try:
        # Streamlit's page context
        if hasattr(st, 'session_state') and 'page' in st.session_state:
            return st.session_state.page
        return None
    except:
        return None


def render_sidebar(expanded: bool = True):
    """
    Render the global sidebar navigation.
    
    Args:
        expanded: Whether sidebar should be expanded by default
    """
    st.sidebar.title("🔬 AetherSignal")
    st.sidebar.caption("Enterprise Pharmacovigilance Platform")
    
    # Group pages by category
    categories = {}
    for page_name, page_info in PAGES.items():
        category = page_info.get("category", "Other")
        if category not in categories:
            categories[category] = []
        categories[category].append((page_name, page_info))
    
    # Render navigation by category
    active_page = get_active_page()
    
    for category in ["Main", "Dashboards", "Data Sources", "AI Tools", "Workflows", "Reports", "Admin"]:
        if category not in categories:
            continue
        
        st.sidebar.markdown(f"### {category}")
        
        for page_name, page_info in categories[category]:
            path = page_info["path"]
            icon = page_info.get("icon", "📄")
            
            # Check if page exists
            page_file = f"pages/{path}.py"
            if not os.path.exists(page_file):
                # Skip if page doesn't exist
                continue
            
            # Determine if active
            is_active = active_page == path or (active_page is None and path == "1_Quantum_PV_Explorer")
            
            # Render link
            if is_active:
                st.sidebar.markdown(f"**{icon} {page_name}**")
            else:
                st.sidebar.markdown(f"{icon} {page_name}")
        
        st.sidebar.markdown("---")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 • Enterprise Ready")


def render_breadcrumbs(page_path: List[str]):
    """
    Render breadcrumb navigation.
    
    Args:
        page_path: List of breadcrumb items (e.g., ["Home", "Dashboards", "Executive"])
    """
    breadcrumb_str = " > ".join(page_path)
    st.markdown(f"**{breadcrumb_str}**")
    st.markdown("---")


def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    breadcrumbs: Optional[List[str]] = None
):
    """
    Render a standard page header.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional icon
        breadcrumbs: Optional breadcrumb path
    """
    if breadcrumbs:
        render_breadcrumbs(breadcrumbs)
    
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)
    
    if subtitle:
        st.caption(subtitle)
    
    st.markdown("---")

