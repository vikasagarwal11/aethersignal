"""
Follow-up logic engine for pharmacovigilance (CHUNK 6.6).
This layer interprets follow-up user goals and returns structured insights
WITHOUT running a full heavy analysis unless required.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def apply_memory_filters(df: pd.DataFrame, memory: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply memory_state filters to the dataframe without recomputing expensive stats.
    This runs instantly in RAM for <100MB datasets.
    """
    if df is None or df.empty:
        return df
    
    filtered = df.copy()

    # Drug filter
    if memory.get("drug"):
        drug = memory["drug"]
        if isinstance(drug, str):
            # Try multiple column names for drug
            drug_cols = ["drug_name", "drug", "drug_concept_name"]
            for col in drug_cols:
                if col in filtered.columns:
                    # Case-insensitive partial match
                    filtered = filtered[filtered[col].astype(str).str.lower().str.contains(drug.lower(), na=False)]
                    break

    # Reactions filter
    if memory.get("reactions"):
        rx_list = memory["reactions"]
        if isinstance(rx_list, list) and len(rx_list) > 0:
            # Try multiple column names for reaction
            reaction_cols = ["reaction", "reaction_pt", "pt", "adverse_reaction"]
            for col in reaction_cols:
                if col in filtered.columns:
                    # Case-insensitive match against list
                    rx_lower = [str(r).lower() for r in rx_list]
                    filtered = filtered[filtered[col].astype(str).str.lower().isin(rx_lower)]
                    break

    # Filters (seriousness, gender, age_group, outcomes)
    for k, v in memory.get("filters", {}).items():
        if v is None:
            continue
        
        # Map memory filter keys to actual column names
        column_mapping = {
            "seriousness": ["serious", "seriousness", "serious_flag"],
            "gender": ["sex", "gender", "gender_concept_id"],
            "age_group": ["age_group", "age"],
            "outcome": ["outcome", "outc_cod", "outcome_concept_id"],
            "country": ["country", "country_code"]
        }
        
        # Find matching column
        cols_to_check = column_mapping.get(k, [k])
        for col in cols_to_check:
            if col in filtered.columns:
                if isinstance(v, bool):
                    # Boolean matching
                    filtered = filtered[filtered[col] == v]
                elif isinstance(v, str):
                    # String matching (case-insensitive)
                    filtered = filtered[filtered[col].astype(str).str.lower() == str(v).lower()]
                else:
                    filtered = filtered[filtered[col] == v]
                break

    # Time window filter
    if memory.get("time_window"):
        # Find date column
        date_cols = ["event_date", "date", "event_date_parsed", "report_date"]
        date_col = None
        for col in date_cols:
            if col in filtered.columns:
                date_col = col
                break
        
        if date_col:
            try:
                filtered = filtered.copy()
                filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
                filtered = filtered.dropna(subset=[date_col])  # Remove invalid dates
                
                if len(filtered) > 0:
                    code = memory["time_window"]
                    max_date = filtered[date_col].max()
                    
                    if code == "6m":
                        cutoff = max_date - pd.DateOffset(months=6)
                        filtered = filtered[filtered[date_col] >= cutoff]
                    elif code == "12m":
                        cutoff = max_date - pd.DateOffset(months=12)
                        filtered = filtered[filtered[date_col] >= cutoff]
                    elif code == "3m":
                        cutoff = max_date - pd.DateOffset(months=3)
                        filtered = filtered[filtered[date_col] >= cutoff]
                    elif code == "1m":
                        cutoff = max_date - pd.DateOffset(months=1)
                        filtered = filtered[filtered[date_col] >= cutoff]
                    elif len(str(code)) == 4 and str(code).isdigit():
                        # Year filter (e.g., "2023")
                        year = int(code)
                        filtered = filtered[filtered[date_col].dt.year == year]
            except Exception:
                # If time filtering fails, return unfiltered
                pass

    return filtered


# ------------------------------------------------------------------------
# QUICK ANALYSIS HELPERS (no heavy ROR/PRR)
# ------------------------------------------------------------------------

def quick_case_count(df: pd.DataFrame) -> int:
    """Get total case count."""
    if df is None or df.empty:
        return 0
    return len(df)


def quick_reaction_summary(df: pd.DataFrame, top_n: int = 10) -> Dict[str, int]:
    """
    Returns reaction frequency summary.
    """
    if df is None or df.empty:
        return {}
    
    # Try multiple column names for reaction
    reaction_cols = ["reaction", "reaction_pt", "pt", "adverse_reaction"]
    reaction_col = None
    for col in reaction_cols:
        if col in df.columns:
            reaction_col = col
            break
    
    if not reaction_col:
        return {}
    
    try:
        # Handle multiple reactions per case (semicolon-separated)
        reactions = df[reaction_col].astype(str).str.split(';').explode()
        reactions = reactions.str.strip()
        reactions = reactions[reactions != 'nan']
        reactions = reactions[reactions != '']
        
        return reactions.value_counts().head(top_n).to_dict()
    except Exception:
        return {}


def quick_age_breakdown(df: pd.DataFrame) -> Dict[str, int]:
    """Get age group breakdown."""
    if df is None or df.empty:
        return {}
    
    # Try multiple column names for age
    age_cols = ["age_group", "age"]
    age_col = None
    for col in age_cols:
        if col in df.columns:
            age_col = col
            break
    
    if not age_col:
        return {}
    
    try:
        return df[age_col].value_counts().to_dict()
    except Exception:
        return {}


def quick_gender_breakdown(df: pd.DataFrame) -> Dict[str, int]:
    """Get gender breakdown."""
    if df is None or df.empty:
        return {}
    
    # Try multiple column names for gender
    gender_cols = ["sex", "gender", "gender_concept_id"]
    gender_col = None
    for col in gender_cols:
        if col in df.columns:
            gender_col = col
            break
    
    if not gender_col:
        return {}
    
    try:
        return df[gender_col].value_counts().to_dict()
    except Exception:
        return {}


def quick_trend(df: pd.DataFrame, months: int = 12) -> Dict[str, Any]:
    """
    A very lightweight trend approximation (monthly counts).
    Enough for conversational responses without heavy stats.
    """
    if df is None or df.empty:
        return {}
    
    # Find date column
    date_cols = ["event_date", "date", "event_date_parsed", "report_date"]
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        return {}
    
    try:
        tmp = df.copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna(subset=[date_col])
        
        if len(tmp) == 0:
            return {}
        
        tmp["month"] = tmp[date_col].dt.to_period("M")
        monthly_counts = tmp.groupby("month").size().tail(months)
        
        # Convert Period to string for JSON serialization
        return {str(period): int(count) for period, count in monthly_counts.items()}
    except Exception:
        return {}


def quick_compare(df: pd.DataFrame, years: int = 3) -> Dict[str, Any]:
    """
    Compare last N years.
    """
    if df is None or df.empty:
        return {}
    
    # Find date column
    date_cols = ["event_date", "date", "event_date_parsed", "report_date"]
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        return {}
    
    try:
        tmp = df.copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna(subset=[date_col])
        
        if len(tmp) == 0:
            return {}
        
        tmp["year"] = tmp[date_col].dt.year
        yearly_counts = tmp.groupby("year").size().tail(years)
        
        # Convert to int keys for JSON serialization
        return {int(year): int(count) for year, count in yearly_counts.items()}
    except Exception:
        return {}


# ------------------------------------------------------------------------
# MAIN FOLLOW-UP ENGINE
# ------------------------------------------------------------------------

def followup_analysis(
    df: pd.DataFrame,
    memory: Dict[str, Any],
    include_all: bool = False
) -> Dict[str, Any]:
    """
    Interprets memory_state.user_goals to produce targeted quick insights.
    These are small/fast computations (milliseconds).
    
    Args:
        df: Full normalized dataframe
        memory: Memory state dictionary
        include_all: If True, include all quick insights regardless of goals
        
    Returns:
        Dictionary with quick analysis results
    """
    if df is None or df.empty:
        return {}
    
    # Apply memory filters first
    filtered = apply_memory_filters(df, memory)
    
    if filtered.empty:
        return {"case_count": 0}
    
    results = {}
    
    goals = memory.get("user_goals", [])
    
    # Always include case count if we have filtered data
    results["case_count"] = quick_case_count(filtered)
    
    # Include other insights based on goals or if include_all is True
    if include_all or "case_count" in goals or "summary" in goals:
        reaction_summary = quick_reaction_summary(filtered)
        if reaction_summary:
            results["reaction_summary"] = reaction_summary
    
    if include_all or "trend_analysis" in goals or "trend" in goals:
        trend = quick_trend(filtered)
        if trend:
            results["trend"] = trend
    
    if include_all or "comparison" in goals or "compare" in goals:
        compare = quick_compare(filtered)
        if compare:
            results["compare"] = compare
    
    # Always include gender breakdown if available (useful for most queries)
    gender_breakdown = quick_gender_breakdown(filtered)
    if gender_breakdown:
        results["gender_breakdown"] = gender_breakdown
    
    # Always include age breakdown if available
    age_breakdown = quick_age_breakdown(filtered)
    if age_breakdown:
        results["age_breakdown"] = age_breakdown
    
    return results

