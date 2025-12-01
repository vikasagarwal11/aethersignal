"""
Local Summary Extractor (CHUNK 7.4 Part 1)
FAST: <1 second summary engine running fully client-side (Pyodide compatible).
Extracts statistical summaries without any server round-trips.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime


def extract_local_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fast local summary extraction - runs fully client-side.
    
    Generates:
    - Case counts and distributions
    - Drug/reaction statistics
    - Demographics
    - Time-based patterns
    - Feature vectors for clustering
    
    Args:
        df: Safety data DataFrame
        
    Returns:
        Dictionary with local summary statistics
    """
    if df is None or df.empty:
        return {
            "total_cases": 0,
            "error": "Empty dataset"
        }
    
    summary: Dict[str, Any] = {}
    
    try:
        # ============================================================
        # BASIC COUNTS
        # ============================================================
        summary["total_cases"] = int(len(df))
        
        # Seriousness counts
        serious_col = _find_column(df, ["serious", "seriousness", "serious_flag", "serious_cod"])
        if serious_col:
            serious_values = df[serious_col]
            if serious_values.dtype == bool:
                summary["serious_cases"] = int(serious_values.sum())
            elif serious_values.dtype in [int, float]:
                summary["serious_cases"] = int((serious_values == 1).sum() + (serious_values == "Y").sum())
            else:
                # Try string matching
                summary["serious_cases"] = int(serious_values.astype(str).str.upper().str.contains("Y|1|TRUE|SERIOUS").sum())
        else:
            summary["serious_cases"] = 0
        
        summary["non_serious_cases"] = summary["total_cases"] - summary["serious_cases"]
        summary["seriousness_pct"] = (
            (summary["serious_cases"] / summary["total_cases"] * 100)
            if summary["total_cases"] > 0 else 0.0
        )
        
        # ============================================================
        # DRUG COUNTS
        # ============================================================
        drug_col = _find_column(df, ["drug", "drug_name", "drug_normalized", "prod_ai", "drugname"])
        if drug_col:
            drug_counts = df[drug_col].value_counts().head(10)
            summary["top_drugs"] = {
                str(k): int(v) for k, v in drug_counts.items()
            }
            summary["unique_drugs"] = int(df[drug_col].nunique())
        else:
            summary["top_drugs"] = {}
            summary["unique_drugs"] = 0
        
        # ============================================================
        # REACTION/PT COUNTS
        # ============================================================
        reaction_col = _find_column(df, ["reaction", "reaction_pt", "reaction_normalized", "pt", "pt_name"])
        if reaction_col:
            reaction_counts = df[reaction_col].value_counts().head(10)
            summary["top_reactions"] = {
                str(k): int(v) for k, v in reaction_counts.items()
            }
            summary["unique_reactions"] = int(df[reaction_col].nunique())
        else:
            summary["top_reactions"] = {}
            summary["unique_reactions"] = 0
        
        # ============================================================
        # OUTCOMES
        # ============================================================
        outcome_col = _find_column(df, ["outcome", "outc_cod", "outcome_code", "fatal"])
        if outcome_col:
            outcome_counts = df[outcome_col].value_counts()
            summary["outcome_distribution"] = {
                str(k): int(v) for k, v in outcome_counts.items()
            }
            
            # Check for fatal outcomes
            fatal_keywords = ["DEATH", "FATAL", "1", "Y"]
            fatal_count = 0
            for keyword in fatal_keywords:
                fatal_count += int(outcome_counts[outcome_counts.index.astype(str).str.upper().str.contains(keyword, na=False)].sum())
            summary["fatal_cases"] = fatal_count
        else:
            summary["outcome_distribution"] = {}
            summary["fatal_cases"] = 0
        
        # ============================================================
        # TIME-BASED PATTERNS
        # ============================================================
        date_col = _find_date_column(df)
        if date_col:
            try:
                df_date = df.copy()
                df_date["_event_date"] = pd.to_datetime(df_date[date_col], errors="coerce")
                df_date = df_date[df_date["_event_date"].notna()]
                
                if len(df_date) > 0:
                    # Monthly timeline (last 12 months)
                    monthly = df_date["_event_date"].dt.to_period("M").value_counts().sort_index().tail(12)
                    summary["recent_timeline"] = {
                        str(k): int(v) for k, v in monthly.items()
                    }
                    
                    # Yearly summary
                    yearly = df_date["_event_date"].dt.year.value_counts().sort_index()
                    summary["yearly_distribution"] = {
                        str(k): int(v) for k, v in yearly.items()
                    }
                    
                    # Date range
                    summary["date_range"] = {
                        "min": str(df_date["_event_date"].min().date()) if pd.notna(df_date["_event_date"].min()) else None,
                        "max": str(df_date["_event_date"].max().date()) if pd.notna(df_date["_event_date"].max()) else None
                    }
            except Exception:
                summary["recent_timeline"] = {}
        
        # ============================================================
        # DEMOGRAPHICS
        # ============================================================
        # Age
        age_col = _find_column(df, ["age", "age_yrs", "age_cod", "patient_age"])
        if age_col:
            try:
                ages = pd.to_numeric(df[age_col], errors="coerce").dropna()
                if len(ages) > 0:
                    summary["age_stats"] = {
                        "mean": float(ages.mean()),
                        "median": float(ages.median()),
                        "min": float(ages.min()),
                        "max": float(ages.max()),
                        "count": int(len(ages))
                    }
                    
                    # Age groups
                    summary["age_groups"] = {
                        "pediatric_<18": int((ages < 18).sum()),
                        "adult_18_64": int(((ages >= 18) & (ages < 65)).sum()),
                        "elderly_≥65": int((ages >= 65).sum())
                    }
            except Exception:
                pass
        
        # Sex/Gender
        sex_col = _find_column(df, ["sex", "gender", "sex_cod", "patient_sex"])
        if sex_col:
            sex_counts = df[sex_col].value_counts()
            summary["sex_ratio"] = {
                str(k): int(v) for k, v in sex_counts.items()
            }
        
        # ============================================================
        # FEATURE VECTOR FOR CLUSTERING
        # ============================================================
        summary["feature_vector"] = {
            "N": summary["total_cases"],
            "SeriousPct": summary["seriousness_pct"] / 100.0 if summary.get("seriousness_pct") else 0.0,
            "FatalPct": (summary.get("fatal_cases", 0) / summary["total_cases"]) if summary["total_cases"] > 0 else 0.0,
            "TopDrug": list(summary.get("top_drugs", {}).keys())[0] if summary.get("top_drugs") else None,
            "TopReaction": list(summary.get("top_reactions", {}).keys())[0] if summary.get("top_reactions") else None,
            "UniqueDrugs": summary.get("unique_drugs", 0),
            "UniqueReactions": summary.get("unique_reactions", 0),
            "DateRangeYears": _calculate_date_range_years(summary.get("date_range", {}))
        }
        
        # ============================================================
        # METADATA
        # ============================================================
        summary["metadata"] = {
            "extraction_time": datetime.utcnow().isoformat(),
            "engine": "local",
            "columns_analyzed": list(df.columns),
            "row_count": int(len(df))
        }
        
    except Exception as e:
        summary["error"] = str(e)
        summary["total_cases"] = len(df) if df is not None else 0
    
    return summary


def _find_column(df: pd.DataFrame, keywords: list) -> Optional[str]:
    """Find column in DataFrame by keywords."""
    if df is None or df.empty:
        return None
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword.lower() in col_lower for keyword in keywords):
            return col
    
    return None


def _find_date_column(df: pd.DataFrame) -> Optional[str]:
    """Find date column in DataFrame."""
    if df is None or df.empty:
        return None
    
    keywords = ["date", "dt", "time", "received", "report", "event", "fda_dt"]
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in keywords):
            # Quick check if it looks like dates
            sample = df[col].dropna().head(5)
            if len(sample) > 0:
                try:
                    pd.to_datetime(sample, errors="raise")
                    return col
                except Exception:
                    continue
    
    return None


def _calculate_date_range_years(date_range: Dict[str, Any]) -> float:
    """Calculate date range in years."""
    if not date_range:
        return 0.0
    
    try:
        min_date = date_range.get("min")
        max_date = date_range.get("max")
        
        if min_date and max_date:
            from datetime import datetime
            min_dt = datetime.fromisoformat(min_date.replace("Z", "+00:00"))
            max_dt = datetime.fromisoformat(max_date.replace("Z", "+00:00"))
            delta = max_dt - min_dt
            return round(delta.days / 365.25, 2)
    except Exception:
        pass
    
    return 0.0

