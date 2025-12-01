"""
Layout Components - Standard page layouts
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from .components.navigation import render_page_header
from .components.feedback import render_empty_state
from .theme import apply_theme


def render_standard_page(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    breadcrumbs: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    show_sidebar: bool = True
):
    """
    Render a standard page layout.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional icon
        breadcrumbs: Optional breadcrumb path
        filters: Optional filter configuration
        show_sidebar: Whether to show sidebar navigation
    """
    # Apply theme
    apply_theme()
    
    # Render header
    render_page_header(title, subtitle, icon, breadcrumbs)
    
    # Render filters if provided
    if filters:
        from .components.filters import render_filter_panel
        selected_filters = render_filter_panel(filters)
        st.session_state["filters"] = selected_filters
        st.markdown("---")
    
    return st.container()


def render_dashboard_layout(
    title: str,
    kpi_metrics: Optional[List[Dict[str, Any]]] = None,
    charts: Optional[List[Dict[str, Any]]] = None,
    tables: Optional[List[Dict[str, Any]]] = None
):
    """
    Render a standard dashboard layout.
    
    Args:
        title: Dashboard title
        kpi_metrics: List of KPI metric definitions
        charts: List of chart definitions
        tables: List of table definitions
    """
    apply_theme()
    
    st.title(title)
    st.markdown("---")
    
    # KPI Metrics
    if kpi_metrics:
        cols = st.columns(len(kpi_metrics))
        for idx, metric in enumerate(kpi_metrics):
            with cols[idx]:
                st.metric(
                    label=metric.get("label", ""),
                    value=metric.get("value", 0),
                    delta=metric.get("delta")
                )
        st.markdown("---")
    
    # Charts
    if charts:
        for chart in charts:
            st.subheader(chart.get("title", ""))
            chart_func = chart.get("render_func")
            if chart_func:
                chart_func()
            st.markdown("---")
    
    # Tables
    if tables:
        for table in tables:
            st.subheader(table.get("title", ""))
            table_data = table.get("data")
            if table_data is not None:
                st.dataframe(table_data, use_container_width=True)
            st.markdown("---")


def render_two_column_layout(
    left_content: callable,
    right_content: callable,
    left_width: int = 2,
    right_width: int = 1
):
    """
    Render a two-column layout.
    
    Args:
        left_content: Function to render left column
        right_content: Function to render right column
        left_width: Left column width ratio
        right_width: Right column width ratio
    """
    col1, col2 = st.columns([left_width, right_width])
    
    with col1:
        left_content()
    
    with col2:
        right_content()

