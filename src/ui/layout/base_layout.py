"""
Base Layout - Foundation wrapper for all pages
"""

import streamlit as st
from typing import Callable, Optional
from .sidebar import render_sidebar_navigation
from .topnav import render_top_nav_bar
from .theme import apply_global_theme
from .state import GlobalState


class BaseLayout:
    """Base layout wrapper for consistent page structure."""
    
    def __init__(self, show_sidebar: bool = True, show_topnav: bool = True):
        self.show_sidebar = show_sidebar
        self.show_topnav = show_topnav
    
    def render(self, page_content: Callable):
        """
        Render a page with the base layout.
        
        Args:
            page_content: Function that renders the page content
        """
        # Initialize global state
        GlobalState.init()
        
        # Apply global theme
        apply_global_theme()
        
        # Render sidebar
        if self.show_sidebar:
            render_sidebar_navigation()
        
        # Render top navigation
        if self.show_topnav:
            render_top_nav_bar()
        
        # Render breadcrumbs if any
        breadcrumbs = st.session_state.get("breadcrumbs", [])
        if breadcrumbs:
            breadcrumb_str = " > ".join([b.get("label", "") for b in breadcrumbs])
            st.markdown(f'<div class="breadcrumb">{breadcrumb_str}</div>', unsafe_allow_html=True)
        
        # Render page content
        page_content()


def render_base_layout(
    page_content: Callable,
    show_sidebar: bool = True,
    show_topnav: bool = True
):
    """
    Convenience function to render a page with base layout.
    
    Args:
        page_content: Function that renders the page content
        show_sidebar: Whether to show sidebar
        show_topnav: Whether to show top navigation
    """
    layout = BaseLayout(show_sidebar=show_sidebar, show_topnav=show_topnav)
    layout.render(page_content)

