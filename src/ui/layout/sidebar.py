"""
Sidebar Navigation Component - Global navigation menu
"""

import streamlit as st
import os
from typing import Optional
from .routes import ROUTES, ADMIN_ROUTES, get_page_route
from .state import GlobalState


def render_sidebar_navigation():
    """
    Render the global sidebar navigation menu.
    """
    GlobalState.init()
    
    # Logo/Brand
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="margin: 0; color: #2563EB;">🔬 AetherSignal</h2>
        <p style="margin: 0; font-size: 0.75rem; color: #64748B;">Enterprise Pharmacovigilance</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Get current page to highlight active item
    current_page = st.session_state.get("current_page", "executive_dashboard")
    
    # Main Navigation
    st.sidebar.markdown("### 🧭 Navigation")
    
    for section_name, section_config in ROUTES.items():
        icon = section_config.get("icon", "📄")
        route = section_config.get("route")
        
        # Check if this section has subpages
        subpages = section_config.get("subpages")
        
        if subpages:
            # Expandable section with subpages
            with st.sidebar.expander(f"{icon} {section_name}", expanded=False):
                for subpage_name, subpage_config in subpages.items():
                    sub_icon = subpage_config.get("icon", "•")
                    sub_route = subpage_config.get("route")
                    sub_page = subpage_config.get("page")
                    
                    # Check if this is the active page
                    is_active = current_page == sub_route or (
                        sub_page and os.path.exists(f"pages/{sub_page}.py")
                    )
                    
                    button_style = "primary" if is_active else "secondary"
                    
                    if st.sidebar.button(
                        f"{sub_icon} {subpage_name}",
                        key=f"nav_{sub_route}",
                        use_container_width=True,
                        type=button_style
                    ):
                        GlobalState.set_page(sub_route)
                        if sub_page:
                            st.switch_page(f"pages/{sub_page}.py")
        else:
            # Single page (no subpages)
            page = section_config.get("page")
            is_active = current_page == route or (
                page and os.path.exists(f"pages/{page}.py")
            )
            
            button_style = "primary" if is_active else "secondary"
            
            if st.sidebar.button(
                f"{icon} {section_name}",
                key=f"nav_{route}",
                use_container_width=True,
                type=button_style
            ):
                GlobalState.set_page(route)
                if page:
                    st.switch_page(f"pages/{page}.py")
    
    st.sidebar.markdown("---")
    
    # SuperAdmin Section
    if GlobalState.is_superadmin():
        st.sidebar.markdown("### ⚙️ SuperAdmin")
        
        for section_name, section_config in ADMIN_ROUTES.items():
            icon = section_config.get("icon", "🔐")
            route = section_config.get("route")
            page = section_config.get("page")
            
            is_active = current_page == route
            
            button_style = "primary" if is_active else "secondary"
            
            if st.sidebar.button(
                f"{icon} {section_name}",
                key=f"admin_{route}",
                use_container_width=True,
                type=button_style
            ):
                GlobalState.set_page(route)
                if page:
                    st.switch_page(f"pages/{page}.py")
        
        st.sidebar.markdown("---")
    
    # Footer
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0; font-size: 0.75rem; color: #94A3B8;">
        <p>v1.0.0</p>
        <p>Enterprise Ready</p>
    </div>
    """, unsafe_allow_html=True)

