"""
Heartbeat progress indicators for Streamlit.
Provides non-blocking status updates during long operations.
"""
import streamlit as st
from typing import Optional, Any


def heartbeat(message: str, placeholder: Optional[Any] = None, delay: float = 0.0) -> None:
    """
    Shows progressive activity messages during longer tasks.
    
    Note: In Streamlit, we don't sleep here as it blocks execution.
    Instead, we update the placeholder and let Streamlit's rerun handle timing.
    
    Args:
        message: Status message to display
        placeholder: Streamlit placeholder (st.empty()) to update
        delay: Delay in seconds (ignored in Streamlit context, kept for API compatibility)
    """
    if placeholder is not None:
        placeholder.info(f"🔄 {message}…")
