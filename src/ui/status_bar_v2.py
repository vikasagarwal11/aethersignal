"""
Status Bar V2 - Clean, display-only status indicator
Shows: Active workspace, processing mode, data status
Designed to be used once near the top of each main page.
"""

from __future__ import annotations
from typing import Optional
import streamlit as st


def render_status_bar_v2() -> None:
    """
    Render a clean status bar showing:
    - Active workspace (with icon)
    - Processing mode (with description)
    - Data status (rows loaded or upload prompt)
    
    This is display-only - no interactive controls.
    Controls remain in the sidebar.
    """
    # --- Read state ---
    workspace = st.session_state.get("active_workspace", "explorer")
    processing_mode = st.session_state.get("processing_mode", "auto")
    df = st.session_state.get("normalized_data")
    
    # --- Workspace labels & icons ---
    workspace_labels = {
        "explorer": ("🔍", "Signal Explorer"),
        "governance": ("🛡️", "Governance & Audit"),
        "inspector": ("👮", "Inspector Simulation"),
        "executive": ("📊", "Executive Dashboard"),
        "quantum": ("⚛️", "Quantum & Advanced"),
        "processing": ("🧬", "Processing & Offline"),
        "social_ae": ("🌐", "Social AE Explorer"),
    }
    
    ws_icon, ws_label = workspace_labels.get(workspace, ("📋", "Unknown Workspace"))
    
    # --- Processing mode labels & help text ---
    mode_labels = {
        "auto": ("🟡 Auto", "System auto-selects local/server/hybrid based on dataset."),
        "server": ("🔴 Server", "All heavy processing done on secure server."),
        "local": ("🔵 Local", "Browser-based processing for eligible workloads."),
        "hybrid": ("🟢 Hybrid", "Mix of local + server for best performance."),
    }
    
    mode_text, mode_help = mode_labels.get(
        processing_mode,
        ("⚪ Unknown", "Processing mode not set; defaulting to Auto."),
    )
    
    # --- Data status ---
    if df is not None:
        try:
            row_count = len(df)
            data_text = f"✅ {row_count:,} rows loaded"
            data_color = "#16a34a"  # green
        except Exception:
            data_text = "✅ Data loaded"
            data_color = "#16a34a"
    else:
        data_text = "📤 No data loaded — upload a dataset to begin"
        data_color = "#6b7280"  # gray
    
    # --- Render bar ---
    st.markdown(
        """
        <hr style="margin-top: 0.5rem; margin-bottom: 0.5rem; border: none; border-top: 1px solid #e5e7eb;">
        """,
        unsafe_allow_html=True,
    )
    
    # Use columns for clean layout
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.markdown(
            f"""
            <div style="
                font-size: 0.9rem;
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
                background-color: #eff6ff;
                color: #1d4ed8;
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
            ">
                <span>{ws_icon}</span>
                <span style="font-weight: 600;">{ws_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="
                font-size: 0.9rem;
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
            ">
                <span>{mode_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if mode_help:
            st.caption(mode_help)
    
    with col3:
        st.markdown(
            f"""
            <div style="
                font-size: 0.9rem;
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
                background-color: #f0fdf4;
                color: {data_color};
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                justify-content: flex-start;
            ">
                <span>{data_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown(
        """
        <hr style="margin-top: 0.5rem; margin-bottom: 0.75rem; border: none; border-top: 1px solid #e5e7eb;">
        """,
        unsafe_allow_html=True,
    )

