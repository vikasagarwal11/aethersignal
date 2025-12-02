"""
Demo Mode Guard - Enforces read-only demo restrictions
Wave 4: Public Demo Portal
"""

import streamlit as st
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def is_demo_mode() -> bool:
    """
    Check if we're in demo mode.
    
    Returns:
        True if demo mode is active
    """
    return st.session_state.get("demo_mode", False)


def enforce_demo_mode(message: Optional[str] = None) -> None:
    """
    Enforce demo mode restrictions - stops execution if write operations attempted.
    
    Args:
        message: Optional custom message to display
    """
    if is_demo_mode():
        msg = message or "⚠️ **Demo Mode**: This is a read-only demonstration. Data modifications are disabled."
        st.warning(msg)
        st.info("💡 This is a public demo. To access full features, please contact us for access.")
        st.stop()


def exit_demo_mode() -> None:
    """
    Exit demo mode and clear demo state.
    """
    if "demo_mode" in st.session_state:
        del st.session_state["demo_mode"]
    if "demo_data_loaded" in st.session_state:
        del st.session_state["demo_data_loaded"]
    
    logger.info("Demo mode exited")


def set_demo_mode(enabled: bool = True) -> None:
    """
    Set demo mode state.
    
    Args:
        enabled: Whether to enable demo mode
    """
    st.session_state["demo_mode"] = enabled
    if enabled:
        logger.info("Demo mode enabled")
    else:
        exit_demo_mode()

