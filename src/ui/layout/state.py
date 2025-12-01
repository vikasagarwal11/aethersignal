"""
Global State Manager - Shared state across all pages
"""

import streamlit as st
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta


class GlobalState:
    """Manages global application state shared across all pages."""
    
    @staticmethod
    def init():
        """Initialize global state with defaults."""
        # User role and authentication
        if "user_role" not in st.session_state:
            st.session_state["user_role"] = "user"  # user | superadmin
        
        if "is_authenticated" not in st.session_state:
            st.session_state["is_authenticated"] = False
        
        # Navigation state
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "executive_dashboard"
        
        if "breadcrumbs" not in st.session_state:
            st.session_state["breadcrumbs"] = []
        
        # Data selection state
        if "selected_drug" not in st.session_state:
            st.session_state["selected_drug"] = None
        
        if "selected_reaction" not in st.session_state:
            st.session_state["selected_reaction"] = None
        
        if "selected_source" not in st.session_state:
            st.session_state["selected_source"] = None
        
        # Date range (default: last 365 days)
        if "date_range_start" not in st.session_state:
            st.session_state["date_range_start"] = (datetime.now() - timedelta(days=365)).date()
        
        if "date_range_end" not in st.session_state:
            st.session_state["date_range_end"] = datetime.now().date()
        
        # Filter state
        if "global_filters" not in st.session_state:
            st.session_state["global_filters"] = {}
        
        # Theme
        if "theme_mode" not in st.session_state:
            st.session_state["theme_mode"] = "light"  # light | dark
        
        # UI preferences
        if "sidebar_expanded" not in st.session_state:
            st.session_state["sidebar_expanded"] = True
        
        if "copilot_open" not in st.session_state:
            st.session_state["copilot_open"] = False
    
    @staticmethod
    def set_drug(drug: str):
        """Set the currently selected drug."""
        st.session_state["selected_drug"] = drug
        GlobalState.add_breadcrumb("Drug", drug)
    
    @staticmethod
    def set_reaction(reaction: str):
        """Set the currently selected reaction."""
        st.session_state["selected_reaction"] = reaction
        GlobalState.add_breadcrumb("Reaction", reaction)
    
    @staticmethod
    def set_date_range(start, end):
        """Set the global date range filter."""
        st.session_state["date_range_start"] = start
        st.session_state["date_range_end"] = end
    
    @staticmethod
    def add_breadcrumb(label: str, value: Optional[str] = None):
        """Add a breadcrumb to the navigation trail."""
        if "breadcrumbs" not in st.session_state:
            st.session_state["breadcrumbs"] = []
        
        breadcrumb = {"label": label, "value": value}
        st.session_state["breadcrumbs"].append(breadcrumb)
    
    @staticmethod
    def clear_breadcrumbs():
        """Clear all breadcrumbs."""
        st.session_state["breadcrumbs"] = []
    
    @staticmethod
    def set_page(page: str):
        """Set the current page."""
        st.session_state["current_page"] = page
        GlobalState.clear_breadcrumbs()
    
    @staticmethod
    def is_superadmin() -> bool:
        """Check if current user is a superadmin."""
        return st.session_state.get("user_role") == "superadmin"
    
    @staticmethod
    def get_filters() -> Dict[str, Any]:
        """Get current global filters."""
        return st.session_state.get("global_filters", {})
    
    @staticmethod
    def set_filter(key: str, value: Any):
        """Set a global filter."""
        if "global_filters" not in st.session_state:
            st.session_state["global_filters"] = {}
        st.session_state["global_filters"][key] = value

