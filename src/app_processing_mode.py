"""
Processing Mode Management (CHUNK 7.1)
Handles server-side, local (Pyodide), and hybrid processing mode configuration.
"""
import streamlit as st
from typing import Tuple, Optional


class ProcessingMode:
    """Processing mode constants."""
    SERVER = "server"
    LOCAL = "local"
    HYBRID = "hybrid"


def browser_supports_local_processing() -> bool:
    """
    Basic browser capability check.
    More advanced checks happen in CHUNK 7.2.
    
    Returns:
        True if browser likely supports local processing
    """
    # Get user agent from session state if available
    user_agent = st.session_state.get("user_agent", "")
    
    if not user_agent:
        # Try to get from JavaScript if available
        try:
            # This will be populated by JavaScript detection in CHUNK 7.2
            pass
        except:
            pass
    
    # Known unsupported browsers
    unsupported = ["Safari", "Mobile", "Edge 18"]
    
    # Check if any unsupported browser is in user agent
    if any(bad in user_agent for bad in unsupported):
        return False
    
    # Default: assume supported (can be refined in CHUNK 7.2)
    return True


def recommend_mode_based_on_file_size(file_size_mb: float) -> Tuple[str, str]:
    """
    Automatic routing rules based on file size.
    
    Rules:
    - < 50 MB: server recommended (best performance for small datasets)
    - 50-200 MB: hybrid recommended (balance of performance and privacy)
    - > 200 MB: local recommended (avoid server overload, privacy-first)
    
    Args:
        file_size_mb: File size in megabytes
        
    Returns:
        Tuple of (recommended_mode, reason)
    """
    if file_size_mb < 50:
        return ProcessingMode.SERVER, "Best performance for small datasets."
    elif file_size_mb <= 200:
        return ProcessingMode.HYBRID, "Recommended for medium datasets. Balances performance and privacy."
    else:
        return ProcessingMode.LOCAL, "Large file — avoid server overload. Privacy-first processing."


def set_processing_mode(mode: str, reason: str = "") -> None:
    """
    Set the processing mode in session state.
    
    Args:
        mode: Processing mode (server/local/hybrid)
        reason: Optional reason for mode selection
    """
    if mode not in [ProcessingMode.SERVER, ProcessingMode.LOCAL, ProcessingMode.HYBRID]:
        raise ValueError(f"Invalid processing mode: {mode}")
    
    st.session_state.processing_mode = mode
    st.session_state.processing_mode_reason = reason


def get_processing_mode() -> str:
    """
    Get current processing mode from session state.
    
    Returns:
        Current processing mode
    """
    return st.session_state.get("processing_mode", ProcessingMode.SERVER)


def get_processing_mode_reason() -> str:
    """
    Get reason for current processing mode.
    
    Returns:
        Reason string
    """
    return st.session_state.get("processing_mode_reason", "")


def should_use_local_processing() -> bool:
    """
    Check if local processing should be used based on current mode.
    
    Returns:
        True if mode is LOCAL or HYBRID
    """
    mode = get_processing_mode()
    return mode in [ProcessingMode.LOCAL, ProcessingMode.HYBRID]


def should_use_server_processing() -> bool:
    """
    Check if server processing should be used based on current mode.
    
    Returns:
        True if mode is SERVER or HYBRID
    """
    mode = get_processing_mode()
    return mode in [ProcessingMode.SERVER, ProcessingMode.HYBRID]


def initialize_processing_mode() -> None:
    """
    Initialize processing mode in session state.
    Should be called in app_helpers.initialize_session_state().
    """
    if "processing_mode" not in st.session_state:
        st.session_state.processing_mode = ProcessingMode.SERVER  # default
    
    if "processing_mode_reason" not in st.session_state:
        st.session_state.processing_mode_reason = "Default: server-side processing"
    
    if "processing_mode_override" not in st.session_state:
        st.session_state.processing_mode_override = False  # User manually overrode?

