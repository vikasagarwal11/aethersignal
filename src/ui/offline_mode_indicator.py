"""
Offline Mode Indicator (CHUNK 7.9)
UI component showing offline/local processing capabilities.
"""
import streamlit as st
from typing import Dict, Any, Optional


def get_offline_state() -> Dict[str, Any]:
    """
    Get current offline/local processing state from session.
    
    Returns:
        Dictionary with offline state information
    """
    return {
        "browser_ok": st.session_state.get("browser_capabilities", {}).get("wasm_supported", False),
        "pyodide_loaded": st.session_state.get("pyodide_loaded", False),
        "local_processing": st.session_state.get("processing_mode", "server") in ["local", "hybrid"],
        "local_datasets_cached": st.session_state.get("local_cache_size", 0) > 0,
        "processing_mode": st.session_state.get("processing_mode", "server"),
        "dataset_profile": st.session_state.get("dataset_profile", {}),
    }


def render_offline_mode_indicator(state: Optional[Dict[str, Any]] = None) -> None:
    """
    Render offline mode indicator in sidebar.
    
    Args:
        state: Optional state dictionary. If None, fetched from session state.
    """
    if state is None:
        state = get_offline_state()
    
    st.sidebar.markdown("### 🛰 Processing Mode")
    
    # Browser capability check
    if not state.get("browser_ok"):
        st.sidebar.error("⚠️ Browser does not support local processing")
        st.sidebar.caption("WASM/Pyodide not available. Using server mode.")
        return
    
    # Pyodide loading status
    if not state.get("pyodide_loaded"):
        st.sidebar.warning("⏳ Pyodide loading…")
        st.sidebar.caption("Initializing local Python runtime...")
    else:
        st.sidebar.success("✅ Pyodide Ready")
        st.sidebar.caption("Local processing available")
    
    # Current processing mode
    mode = state.get("processing_mode", "server")
    mode_display = {
        "local": "🔵 Local (Offline)",
        "hybrid": "🟡 Hybrid (Local + Server)",
        "server": "🔴 Server Only"
    }.get(mode, "🔴 Server Only")
    
    st.sidebar.info(f"**Current Mode:** {mode_display}")
    
    # Dataset cache status
    if state.get("local_datasets_cached"):
        cache_size = st.session_state.get("local_cache_size", 0)
        st.sidebar.success(f"💾 Local dataset cached ({cache_size:,} rows)")
    else:
        st.sidebar.info("💾 No local dataset cache")
    
    # Dataset profile info
    profile = state.get("dataset_profile", {})
    if profile:
        row_count = profile.get("row_count", 0)
        size_mb = profile.get("file_size_mb", 0)
        
        if row_count > 0:
            st.sidebar.caption(f"Dataset: {row_count:,} rows ({size_mb:.1f} MB)")
    
    # Mode recommendation
    if mode == "server" and state.get("browser_ok") and state.get("pyodide_loaded"):
        with st.sidebar.expander("💡 Switch to Local Mode?"):
            st.caption("Your browser supports local processing. This can reduce server load and enable offline work.")
            if st.button("Enable Local Mode", key="enable_local_mode"):
                st.session_state["processing_mode_preference"] = "local"
                st.rerun()

