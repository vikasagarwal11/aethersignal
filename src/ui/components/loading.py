"""
Loading Components - Spinners, skeletons, progress indicators
"""

import streamlit as st
from typing import Optional


def render_loading_spinner(message: str = "Loading...", use_container_width: bool = False):
    """
    Render a loading spinner.
    
    Args:
        message: Loading message
        use_container_width: Use full container width
    """
    with st.spinner(message):
        st.empty()


def render_skeleton(rows: int = 5, columns: int = 3):
    """
    Render a skeleton loading screen.
    
    Args:
        rows: Number of skeleton rows
        columns: Number of skeleton columns
    """
    for _ in range(rows):
        cols = st.columns(columns)
        for col in cols:
            with col:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                            background-size: 200% 100%;
                            animation: loading 1.5s infinite;
                            height: 40px;
                            border-radius: 4px;
                            margin: 5px 0;">
                </div>
                <style>
                @keyframes loading {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
                </style>
                """, unsafe_allow_html=True)


def render_progress(
    current: int,
    total: int,
    label: Optional[str] = None,
    show_percentage: bool = True
):
    """
    Render a progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        label: Optional label
        show_percentage: Show percentage
    """
    if total == 0:
        return
    
    progress = current / total
    percentage = int(progress * 100)
    
    if label:
        st.caption(label)
    
    st.progress(progress)
    
    if show_percentage:
        st.caption(f"{percentage}% ({current}/{total})")


def render_loading_overlay(message: str = "Processing..."):
    """
    Render a full-page loading overlay.
    
    Args:
        message: Loading message
    """
    st.markdown(f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.5); z-index: 9999; display: flex;
                align-items: center; justify-content: center;">
        <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
            <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db;
                                         border-radius: 50%; width: 40px; height: 40px;
                                         animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
            <p>{message}</p>
        </div>
    </div>
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

