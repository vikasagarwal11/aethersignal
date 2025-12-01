"""
Feedback Components - Alerts, notifications, empty states
"""

import streamlit as st
from typing import Optional, Dict, Any


def render_error(message: str, details: Optional[str] = None, icon: str = "❌"):
    """
    Render an error message.
    
    Args:
        message: Error message
        details: Optional detailed error information
        icon: Error icon
    """
    st.error(f"{icon} **Error:** {message}")
    if details:
        with st.expander("Details"):
            st.code(details)


def render_success(message: str, icon: str = "✅"):
    """
    Render a success message.
    
    Args:
        message: Success message
        icon: Success icon
    """
    st.success(f"{icon} {message}")


def render_warning(message: str, icon: str = "⚠️"):
    """
    Render a warning message.
    
    Args:
        message: Warning message
        icon: Warning icon
    """
    st.warning(f"{icon} {message}")


def render_info(message: str, icon: str = "ℹ️"):
    """
    Render an info message.
    
    Args:
        message: Info message
        icon: Info icon
    """
    st.info(f"{icon} {message}")


def render_empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_callback: Optional[callable] = None
):
    """
    Render an empty state message.
    
    Args:
        title: Empty state title
        message: Empty state message
        icon: Icon to display
        action_label: Optional action button label
        action_callback: Optional action callback
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 40px;">
        <div style="font-size: 48px; margin-bottom: 16px;">{icon}</div>
        <h3>{title}</h3>
        <p style="color: #666;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, use_container_width=True):
                action_callback()


def render_tooltip(text: str, tooltip: str):
    """
    Render text with a tooltip.
    
    Args:
        text: Text to display
        tooltip: Tooltip content
    """
    st.markdown(f"""
    <span title="{tooltip}">{text} ℹ️</span>
    """, unsafe_allow_html=True)

