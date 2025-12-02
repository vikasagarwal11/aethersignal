"""
Workspace Status Bar Component
Shows current workspace and processing mode with quick access controls.
"""
import streamlit as st
from typing import Optional, Dict


def render_workspace_status_bar() -> None:
    """
    Render status bar showing current workspace and processing mode.
    Appears at top of main content area for clear visibility.
    """
    workspace = st.session_state.get("active_workspace", "explorer")
    processing_mode = st.session_state.get("processing_mode", "auto")
    
    # Workspace labels
    workspace_labels = {
        "explorer": "Signal Explorer",
        "governance": "Governance & Audit",
        "inspector": "Inspector Simulation",
        "executive": "Executive Dashboard",
        "quantum": "Quantum & Advanced",
        "processing": "Processing & Offline",
    }
    
    # Workspace icons
    workspace_icons = {
        "explorer": "🔍",
        "governance": "🛡️",
        "inspector": "👮",
        "executive": "📊",
        "quantum": "⚛️",
        "processing": "🧬",
    }
    
    # Processing mode labels and colors
    mode_labels = {
        "auto": ("Auto", "🟡", "System auto-selects best mode"),
        "server": ("Server", "🔴", "All processing on server"),
        "local": ("Local", "🔵", "Browser-based processing"),
        "hybrid": ("Hybrid", "🟢", "Mixed local + server"),
    }
    
    mode_label, mode_icon, mode_tooltip = mode_labels.get(
        processing_mode, 
        ("Unknown", "⚪", "Processing mode not set")
    )
    
    current_workspace_label = workspace_labels.get(workspace, "Unknown Workspace")
    current_workspace_icon = workspace_icons.get(workspace, "📋")
    
    # Render status bar
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        # Workspace indicator with quick switcher
        st.markdown(f"**{current_workspace_icon} Active Workspace:** {current_workspace_label}")
        
        # Quick workspace switcher dropdown
        with st.popover("🔀 Switch Workspace", help="Quick switch to different workspace"):
            workspace_options = list(workspace_labels.items())
            selected_option = st.selectbox(
                "Select workspace:",
                options=[label for _, label in workspace_options],
                index=[k for k, _ in workspace_options].index(workspace) if workspace in [k for k, _ in workspace_options] else 0,
                key="quick_workspace_switch"
            )
            
            # Find the key for selected label
            selected_key = None
            for key, label in workspace_options:
                if label == selected_option:
                    selected_key = key
                    break
            
            if selected_key and selected_key != workspace:
                if st.button("Switch", key="confirm_workspace_switch", type="primary"):
                    st.session_state.active_workspace = selected_key
                    st.rerun()
    
    with col2:
        # Processing mode indicator
        st.markdown(f"**{mode_icon} Processing Mode:** {mode_label}")
        st.caption(mode_tooltip)
    
    with col3:
        # Quick link to processing workspace
        if processing_mode != "auto":
            if st.button("⚙️ Change Mode", key="goto_processing", use_container_width=True):
                st.session_state.active_workspace = "processing"
                st.rerun()
    
    with col4:
        # Data status indicator
        data_loaded = st.session_state.data is not None and st.session_state.normalized_data is not None
        if data_loaded:
            df = st.session_state.normalized_data
            st.success(f"✅ {len(df):,} rows")
        else:
            st.info("📤 Upload data")
    
    st.markdown("---")

