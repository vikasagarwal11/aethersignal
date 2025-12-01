"""
UI Layout System - Global navigation, routing, and layout foundation
"""

from .base_layout import render_base_layout, BaseLayout
from .sidebar import render_sidebar_navigation
from .topnav import render_top_nav_bar
from .theme import apply_global_theme, get_theme_colors
from .state import GlobalState
from .routes import ROUTES, ADMIN_ROUTES, get_page_route

__all__ = [
    "render_base_layout",
    "BaseLayout",
    "render_sidebar_navigation",
    "render_top_nav_bar",
    "apply_global_theme",
    "get_theme_colors",
    "GlobalState",
    "ROUTES",
    "ADMIN_ROUTES",
    "get_page_route"
]

