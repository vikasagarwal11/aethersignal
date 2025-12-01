"""
Multi-Layer Heatmap Filters (CHUNK A6)
Interactive filtering system for governance heatmap.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


def render_heatmap_filters(
    heatmap_df: pd.DataFrame,
    signals: Optional[List[Dict[str, Any]]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Render multi-layer filter controls and apply filters to heatmap DataFrame.
    
    Args:
        heatmap_df: Original heatmap DataFrame
        signals: List of signal dictionaries (for extracting metadata)
        
    Returns:
        Tuple of (filtered DataFrame, filter settings dictionary)
    """
    if heatmap_df is None or heatmap_df.empty:
        return heatmap_df, {}
    
    st.markdown("### ⚙️ Heatmap Filters")
    
    with st.expander("🔍 Filter Options", expanded=True):
        filter_settings = {}
        
        # A6.1 - Therapeutic Area Filter
        therapeutic_areas = _extract_therapeutic_areas(signals) if signals else []
        if therapeutic_areas:
            selected_ta = st.multiselect(
                "Therapeutic Area",
                options=therapeutic_areas,
                default=[],
                help="Filter signals by therapeutic area"
            )
            filter_settings["therapeutic_areas"] = selected_ta
        else:
            filter_settings["therapeutic_areas"] = []
        
        # A6.2 - Severity Level Filter
        selected_severity = st.multiselect(
            "Severity Level",
            options=["Low", "Medium", "High", "Critical"],
            default=[],
            help="Filter by signal severity level"
        )
        filter_settings["severity"] = selected_severity
        
        # A6.3 - Lifecycle Stage Filter
        lifecycle_stages = ["Triage", "Validation", "Assessment", "Evaluation", "Recommendation", "CAPA", "Closed"]
        selected_lifecycle = st.multiselect(
            "Lifecycle Stage",
            options=lifecycle_stages,
            default=[],
            help="Filter by signal lifecycle stage"
        )
        filter_settings["lifecycle_stage"] = selected_lifecycle
        
        # A6.4 - Reviewer Filter
        reviewers = _extract_reviewers(signals) if signals else []
        if reviewers:
            selected_reviewer = st.multiselect(
                "Assigned Reviewer",
                options=reviewers,
                default=[],
                help="Filter by assigned reviewer"
            )
            filter_settings["reviewer"] = selected_reviewer
        else:
            filter_settings["reviewer"] = []
        
        # A6.5 - Signal Confidence Score (SCS) Filter
        selected_scs = st.slider(
            "Signal Confidence Score (SCS) Range",
            0.0,
            1.0,
            (0.0, 1.0),
            step=0.05,
            help="Filter by confidence score range"
        )
        filter_settings["scs_range"] = selected_scs
        
        # Apply filters
        filtered_df = apply_heatmap_filters(heatmap_df, filter_settings, signals)
        
        # Display filter summary
        if any(filter_settings.values()):
            active_filters = []
            if filter_settings.get("therapeutic_areas"):
                active_filters.append(f"TA: {', '.join(filter_settings['therapeutic_areas'])}")
            if filter_settings.get("severity"):
                active_filters.append(f"Severity: {', '.join(filter_settings['severity'])}")
            if filter_settings.get("lifecycle_stage"):
                active_filters.append(f"Lifecycle: {', '.join(filter_settings['lifecycle_stage'])}")
            if filter_settings.get("reviewer"):
                active_filters.append(f"Reviewer: {', '.join(filter_settings['reviewer'])}")
            
            scs_range = filter_settings.get("scs_range", (0.0, 1.0))
            if scs_range != (0.0, 1.0):
                active_filters.append(f"SCS: {scs_range[0]:.2f}-{scs_range[1]:.2f}")
            
            if active_filters:
                st.info(f"🔍 Active Filters: {', '.join(active_filters)} | Showing {len(filtered_df)} of {len(heatmap_df)} items")
        
        return filtered_df, filter_settings


def apply_heatmap_filters(
    heatmap_df: pd.DataFrame,
    filter_settings: Dict[str, Any],
    signals: Optional[List[Dict[str, Any]]] = None
) -> pd.DataFrame:
    """
    Apply filters to heatmap DataFrame.
    
    Args:
        heatmap_df: Original heatmap DataFrame
        filter_settings: Dictionary of filter settings
        signals: List of signal dictionaries for metadata lookup
        
    Returns:
        Filtered DataFrame
    """
    if heatmap_df is None or heatmap_df.empty:
        return heatmap_df
    
    filtered_df = heatmap_df.copy()
    
    # Build signal metadata map for filtering
    signal_metadata = {}
    if signals:
        for signal in signals:
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", signal.get("event", "Unknown"))
            key = f"{drug} - {reaction}"
            signal_metadata[key] = signal
    
    # A6.1 - Therapeutic Area Filter
    if filter_settings.get("therapeutic_areas"):
        ta_list = filter_settings["therapeutic_areas"]
        # Filter rows by therapeutic area
        filtered_indices = []
        for idx in filtered_df.index:
            signal_key = str(idx)
            signal = signal_metadata.get(signal_key, {})
            ta = signal.get("therapeutic_area", "")
            if ta in ta_list:
                filtered_indices.append(idx)
        if filtered_indices:
            filtered_df = filtered_df.loc[filtered_indices]
        else:
            # No matches, return empty DataFrame
            return pd.DataFrame()
    
    # A6.2 - Severity Filter
    if filter_settings.get("severity"):
        severity_list = filter_settings["severity"]
        # Filter by severity in RPF Priority or other columns
        filtered_indices = []
        for idx in filtered_df.index:
            signal_key = str(idx)
            signal = signal_metadata.get(signal_key, {})
            priority = signal.get("priority", signal.get("qsp_priority", "Low"))
            if priority in severity_list or any(s in str(priority) for s in severity_list):
                filtered_indices.append(idx)
        if filtered_indices:
            filtered_df = filtered_df.loc[filtered_indices]
        else:
            return pd.DataFrame()
    
    # A6.3 - Lifecycle Stage Filter
    if filter_settings.get("lifecycle_stage"):
        lifecycle_list = filter_settings["lifecycle_stage"]
        # Check Lifecycle Stage column in heatmap
        if "Lifecycle Stage" in filtered_df.columns:
            # Filter by lifecycle level
            mask = filtered_df["Lifecycle Stage"].apply(
                lambda x: any(lc.lower() in str(x).lower() for lc in lifecycle_list)
            )
            filtered_df = filtered_df[mask]
        else:
            # Fallback: filter by signal metadata
            filtered_indices = []
            for idx in filtered_df.index:
                signal_key = str(idx)
                signal = signal_metadata.get(signal_key, {})
                lifecycle = signal.get("lifecycle", signal.get("status", ""))
                if any(lc.lower() in str(lifecycle).lower() for lc in lifecycle_list):
                    filtered_indices.append(idx)
            if filtered_indices:
                filtered_df = filtered_df.loc[filtered_indices]
            else:
                return pd.DataFrame()
    
    # A6.4 - Reviewer Filter
    if filter_settings.get("reviewer"):
        reviewer_list = filter_settings["reviewer"]
        filtered_indices = []
        for idx in filtered_df.index:
            signal_key = str(idx)
            signal = signal_metadata.get(signal_key, {})
            reviewer = signal.get("owner", signal.get("reviewer", ""))
            if reviewer in reviewer_list:
                filtered_indices.append(idx)
        if filtered_indices:
            filtered_df = filtered_df.loc[filtered_indices]
        else:
            return pd.DataFrame()
    
    # A6.5 - Signal Confidence Score (SCS) Filter
    scs_range = filter_settings.get("scs_range", (0.0, 1.0))
    if scs_range != (0.0, 1.0):
        low_scs, high_scs = scs_range
        filtered_indices = []
        for idx in filtered_df.index:
            signal_key = str(idx)
            signal = signal_metadata.get(signal_key, {})
            scs = signal.get("confidence_score", signal.get("signal_confidence", 0))
            if isinstance(scs, (int, float)):
                scs_normalized = scs / 100.0 if scs > 1 else scs
                if low_scs <= scs_normalized <= high_scs:
                    filtered_indices.append(idx)
        if filtered_indices:
            filtered_df = filtered_df.loc[filtered_indices]
        else:
            return pd.DataFrame()
    
    return filtered_df


def _extract_therapeutic_areas(signals: List[Dict[str, Any]]) -> List[str]:
    """Extract unique therapeutic areas from signals."""
    tas = set()
    
    for signal in signals:
        ta = signal.get("therapeutic_area", signal.get("indication", ""))
        if ta:
            tas.add(str(ta))
    
    # If no explicit TA, try to infer from drug/reaction
    if not tas:
        for signal in signals:
            drug = signal.get("drug", "").lower()
            if any(term in drug for term in ["dupixent", "adalimumab", "etanercept"]):
                tas.add("Dermatology/Immunology")
            elif any(term in drug for term in ["keytruda", "opdivo", "yervoy"]):
                tas.add("Oncology")
            elif any(term in drug for term in ["metformin", "insulin", "glipizide"]):
                tas.add("Cardiometabolic")
    
    return sorted(list(tas)) if tas else []


def _extract_reviewers(signals: List[Dict[str, Any]]) -> List[str]:
    """Extract unique reviewers from signals."""
    reviewers = set()
    
    for signal in signals:
        reviewer = signal.get("owner", signal.get("reviewer", signal.get("assigned_reviewer", "")))
        if reviewer:
            reviewers.add(str(reviewer))
    
    return sorted(list(reviewers)) if reviewers else []

