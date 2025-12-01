"""
Dataset Profiler (CHUNK H1.2)
Analyzes datasets to create profiles used by Hybrid Mode Manager for mode selection.
Profiles include file size, row count, memory footprint, drug/reaction counts, and time ranges.
"""
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def profile_dataframe(df: pd.DataFrame, file_size_mb: Optional[float] = None) -> Dict[str, Any]:
    """
    Profile a DataFrame and create a dataset profile for hybrid mode selection.
    
    Args:
        df: Pandas DataFrame to profile
        file_size_mb: Original file size in MB (if known)
        
    Returns:
        Dictionary with dataset profile containing:
        - file_size_mb: float
        - row_count: int
        - column_count: int
        - drug_count: int
        - reaction_count: int
        - date_range_years: float
        - memory_footprint_mb: float
        - unique_cases: int
        - avg_fields_per_row: float
        - has_temporal_data: bool
    """
    if df is None or df.empty:
        return {
            "file_size_mb": file_size_mb or 0.0,
            "row_count": 0,
            "column_count": 0,
            "drug_count": 0,
            "reaction_count": 0,
            "date_range_years": 0.0,
            "memory_footprint_mb": 0.0,
            "unique_cases": 0,
            "avg_fields_per_row": 0.0,
            "has_temporal_data": False,
            "data_type": "empty"
        }
    
    profile = {}
    
    # Basic counts
    profile["row_count"] = len(df)
    profile["column_count"] = len(df.columns)
    
    # Memory footprint (approximate)
    memory_bytes = df.memory_usage(deep=True).sum()
    profile["memory_footprint_mb"] = memory_bytes / (1024 * 1024)
    
    # File size (use provided or estimate from memory)
    if file_size_mb:
        profile["file_size_mb"] = file_size_mb
    else:
        # Estimate from memory footprint (usually compressed on disk)
        profile["file_size_mb"] = profile["memory_footprint_mb"] * 0.3  # Rough compression estimate
    
    # Drug count
    drug_cols = ["drug_normalized", "drug_name", "drug", "drug_concept_name"]
    drug_col = next((col for col in drug_cols if col in df.columns), None)
    if drug_col:
        profile["drug_count"] = df[drug_col].nunique()
    else:
        profile["drug_count"] = 0
    
    # Reaction count
    reaction_cols = ["reaction_normalized", "reaction_pt", "reaction", "pt", "adverse_reaction"]
    reaction_col = next((col for col in reaction_cols if col in df.columns), None)
    if reaction_col:
        profile["reaction_count"] = df[reaction_col].nunique()
    else:
        profile["reaction_count"] = 0
    
    # Unique cases
    case_cols = ["primaryid", "caseid", "ISR", "CASE", "case_id"]
    case_col = next((col for col in case_cols if col in df.columns), None)
    if case_col:
        profile["unique_cases"] = df[case_col].nunique()
    else:
        profile["unique_cases"] = profile["row_count"]  # Assume one row = one case if no case ID
    
    # Date range (temporal data)
    date_cols = ["event_date", "event_dt", "report_date", "received_date", "date"]
    date_col = next((col for col in date_cols if col in df.columns), None)
    
    profile["has_temporal_data"] = date_col is not None
    profile["date_range_years"] = 0.0
    
    if date_col:
        try:
            df_dates = pd.to_datetime(df[date_col], errors='coerce')
            df_dates_clean = df_dates.dropna()
            if not df_dates_clean.empty:
                date_min = df_dates_clean.min()
                date_max = df_dates_clean.max()
                date_range = (date_max - date_min).days / 365.25
                profile["date_range_years"] = date_range
        except Exception:
            pass
    
    # Average fields per row (non-null values)
    profile["avg_fields_per_row"] = df.notna().sum(axis=1).mean() if not df.empty else 0.0
    
    # Data type classification
    if profile["row_count"] == 0:
        profile["data_type"] = "empty"
    elif profile["drug_count"] > 0 and profile["reaction_count"] > 0:
        profile["data_type"] = "pv_cases"  # Pharmacovigilance cases
    elif profile["has_temporal_data"]:
        profile["data_type"] = "time_series"
    else:
        profile["data_type"] = "tabular"
    
    # Complexity score (0-1, higher = more complex)
    complexity = 0.0
    if profile["row_count"] > 0:
        complexity += min(0.4, profile["row_count"] / 10_000_000)  # Up to 0.4 from row count
    if profile["column_count"] > 0:
        complexity += min(0.2, profile["column_count"] / 100)  # Up to 0.2 from column count
    if profile["memory_footprint_mb"] > 0:
        complexity += min(0.3, profile["memory_footprint_mb"] / 500)  # Up to 0.3 from memory
    if profile["has_temporal_data"]:
        complexity += 0.1  # Temporal adds complexity
    
    profile["complexity_score"] = min(1.0, complexity)
    
    # Timestamp
    profile["profiled_at"] = datetime.now().isoformat()
    
    return profile


def profile_from_file_info(
    file_size_bytes: int,
    file_name: Optional[str] = None,
    file_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a basic profile from file information (before loading).
    
    Useful for mode selection before data is loaded.
    
    Args:
        file_size_bytes: File size in bytes
        file_name: Optional file name for type detection
        file_type: Optional file type (csv, xlsx, zip, etc.)
        
    Returns:
        Basic profile dictionary
    """
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    profile = {
        "file_size_mb": file_size_mb,
        "file_name": file_name,
        "file_type": file_type,
        "row_count": None,  # Unknown until loaded
        "column_count": None,
        "drug_count": None,
        "reaction_count": None,
        "date_range_years": None,
        "memory_footprint_mb": file_size_mb * 2.0,  # Estimate: in-memory is ~2x file size
        "unique_cases": None,
        "avg_fields_per_row": None,
        "has_temporal_data": None,
        "complexity_score": min(1.0, file_size_mb / 500.0),  # Estimate based on size
        "profiled_at": datetime.now().isoformat(),
        "profile_type": "file_info_only"
    }
    
    return profile


def estimate_profile_from_sample(
    df_sample: pd.DataFrame,
    total_row_count: Optional[int] = None,
    file_size_mb: Optional[float] = None
) -> Dict[str, Any]:
    """
    Estimate full dataset profile from a sample.
    
    Useful when processing large files in chunks.
    
    Args:
        df_sample: Sample DataFrame (first N rows)
        total_row_count: Total rows in full dataset (if known)
        file_size_mb: Total file size in MB (if known)
        
    Returns:
        Estimated profile dictionary
    """
    if df_sample is None or df_sample.empty:
        return profile_from_file_info(0, None, None)
    
    # Profile the sample
    sample_profile = profile_dataframe(df_sample, file_size_mb=None)
    
    # Scale up if we know total row count
    if total_row_count and sample_profile["row_count"] > 0:
        scale_factor = total_row_count / sample_profile["row_count"]
        
        sample_profile["row_count"] = total_row_count
        sample_profile["memory_footprint_mb"] = sample_profile["memory_footprint_mb"] * scale_factor
        
        # Estimate unique counts (conservative: won't scale linearly)
        if sample_profile["drug_count"] > 0:
            sample_profile["drug_count"] = int(sample_profile["drug_count"] * min(scale_factor, 10.0))
        if sample_profile["reaction_count"] > 0:
            sample_profile["reaction_count"] = int(sample_profile["reaction_count"] * min(scale_factor, 10.0))
    
    # Use provided file size if available
    if file_size_mb:
        sample_profile["file_size_mb"] = file_size_mb
    
    sample_profile["profile_type"] = "estimated_from_sample"
    
    return sample_profile


def get_profile_for_mode_selection(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only the fields needed for hybrid mode selection.
    
    Args:
        profile: Full dataset profile
        
    Returns:
        Simplified profile for mode manager
    """
    return {
        "file_size_mb": profile.get("file_size_mb", 0),
        "row_count": profile.get("row_count", 0),
        "memory_footprint_mb": profile.get("memory_footprint_mb", profile.get("file_size_mb", 0) * 2),
        "drug_count": profile.get("drug_count", 0),
        "reaction_count": profile.get("reaction_count", 0),
        "date_range_years": profile.get("date_range_years", 0.0),
        "column_count": profile.get("column_count", 0)
    }

