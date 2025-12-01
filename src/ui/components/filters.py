"""
Filter Components - Filter panels, quick filters, saved presets
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


FILTER_STORAGE = Path("data/filters")


def render_filter_panel(
    filters: Dict[str, Any],
    on_change: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Render a filter panel.
    
    Args:
        filters: Dictionary of filter definitions
        on_change: Optional callback when filters change
    
    Returns:
        Dictionary of selected filter values
    """
    FILTER_STORAGE.mkdir(parents=True, exist_ok=True)
    
    selected = {}
    
    with st.expander("🔍 Filters", expanded=False):
        for filter_name, filter_config in filters.items():
            filter_type = filter_config.get("type", "text")
            label = filter_config.get("label", filter_name)
            options = filter_config.get("options", [])
            default = filter_config.get("default", None)
            
            if filter_type == "text":
                value = st.text_input(label, value=default or "")
                selected[filter_name] = value
            
            elif filter_type == "select":
                value = st.selectbox(label, options, index=0 if default in options else 0)
                selected[filter_name] = value
            
            elif filter_type == "multiselect":
                value = st.multiselect(label, options, default=default or [])
                selected[filter_name] = value
            
            elif filter_type == "date_range":
                col1, col2 = st.columns(2)
                with col1:
                    start = st.date_input(f"{label} (Start)", value=default.get("start") if default else None)
                with col2:
                    end = st.date_input(f"{label} (End)", value=default.get("end") if default else None)
                selected[filter_name] = {"start": start, "end": end}
            
            elif filter_type == "slider":
                min_val = filter_config.get("min", 0)
                max_val = filter_config.get("max", 100)
                value = st.slider(label, min_val, max_val, value=default or min_val)
                selected[filter_name] = value
    
    return selected


def render_quick_filters(
    filters: List[Dict[str, Any]],
    active_filter: Optional[str] = None
) -> Optional[str]:
    """
    Render quick filter chips.
    
    Args:
        filters: List of filter definitions
        active_filter: Currently active filter
    
    Returns:
        Selected filter key or None
    """
    cols = st.columns(len(filters))
    selected = None
    
    for idx, filter_def in enumerate(filters):
        with cols[idx]:
            key = filter_def.get("key")
            label = filter_def.get("label", key)
            is_active = active_filter == key
            
            if st.button(
                label,
                key=f"quick_filter_{key}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                selected = key
    
    return selected


def save_filter_preset(name: str, filters: Dict[str, Any], user_id: Optional[str] = None):
    """
    Save a filter preset.
    
    Args:
        name: Preset name
        filters: Filter values
        user_id: Optional user ID
    """
    FILTER_STORAGE.mkdir(parents=True, exist_ok=True)
    
    preset_file = FILTER_STORAGE / f"{name}_{user_id or 'default'}.json"
    
    try:
        with open(preset_file, "w") as f:
            json.dump(filters, f)
        return True
    except Exception:
        return False


def load_filter_preset(name: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load a filter preset.
    
    Args:
        name: Preset name
        user_id: Optional user ID
    
    Returns:
        Filter values or None
    """
    preset_file = FILTER_STORAGE / f"{name}_{user_id or 'default'}.json"
    
    if not preset_file.exists():
        return None
    
    try:
        with open(preset_file, "r") as f:
            return json.load(f)
    except Exception:
        return None

