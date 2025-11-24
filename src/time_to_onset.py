"""
Time-to-onset analysis for AetherSignal.
Calculates time-to-onset distributions and Weibull parameters for drug-reaction pairs.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.optimize import minimize
from src.utils import parse_date, safe_divide


def calculate_time_to_onset(
    df: pd.DataFrame,
    drug_col: str = "drug_name",
    reaction_col: str = "reaction",
    start_date_col: str = "start_date",
    onset_date_col: str = "onset_date"
) -> pd.DataFrame:
    """
    Calculate time-to-onset (TTO) for each case.
    
    Args:
        df: DataFrame with case data
        drug_col: Column name for drug
        reaction_col: Column name for reaction
        start_date_col: Column name for drug start date
        onset_date_col: Column name for reaction onset date
    
    Returns:
        DataFrame with TTO in days added as 'tto_days' column
    """
    result_df = df.copy()
    
    # Parse dates
    start_dates = result_df[start_date_col].apply(parse_date) if start_date_col in result_df.columns else None
    onset_dates = result_df[onset_date_col].apply(parse_date) if onset_date_col in result_df.columns else None
    
    # Calculate TTO
    tto_days = []
    for idx, row in result_df.iterrows():
        start_date = start_dates.iloc[idx] if start_dates is not None else None
        onset_date = onset_dates.iloc[idx] if onset_dates is not None else None
        
        if start_date and onset_date and pd.notna(start_date) and pd.notna(onset_date):
            tto = (onset_date - start_date).days
            if tto >= 0:  # Only include valid TTO (onset after start)
                tto_days.append(tto)
            else:
                tto_days.append(np.nan)
        else:
            tto_days.append(np.nan)
    
    result_df["tto_days"] = tto_days
    return result_df


def fit_weibull(tto_data: pd.Series) -> Dict[str, float]:
    """
    Fit Weibull distribution to time-to-onset data.
    
    Args:
        tto_data: Series of time-to-onset values in days (non-negative)
    
    Returns:
        Dictionary with Weibull parameters: shape, scale, mean, median, and fit statistics
    """
    # Remove NaN and negative values
    clean_data = tto_data.dropna()
    clean_data = clean_data[clean_data >= 0]
    
    if len(clean_data) < 3:
        return {
            "shape": np.nan,
            "scale": np.nan,
            "mean": np.nan,
            "median": np.nan,
            "n": len(clean_data),
            "fit_success": False
        }
    
    try:
        # Fit Weibull distribution using scipy
        # Weibull parameters: shape (c) and scale (lambda)
        shape, loc, scale = stats.weibull_min.fit(clean_data, floc=0)  # Force location=0
        
        # Calculate statistics
        mean = scale * np.math.gamma(1 + 1/shape) if shape > 0 else np.nan
        median = scale * (np.log(2) ** (1/shape)) if shape > 0 else np.nan
        
        # Goodness of fit (Kolmogorov-Smirnov test)
        ks_stat, ks_pvalue = stats.kstest(clean_data, lambda x: stats.weibull_min.cdf(x, shape, loc=0, scale=scale))
        
        return {
            "shape": float(shape),
            "scale": float(scale),
            "mean": float(mean) if not np.isnan(mean) else np.nan,
            "median": float(median) if not np.isnan(median) else np.nan,
            "n": len(clean_data),
            "ks_statistic": float(ks_stat),
            "ks_pvalue": float(ks_pvalue),
            "fit_success": True
        }
    except Exception as e:
        return {
            "shape": np.nan,
            "scale": np.nan,
            "mean": np.nan,
            "median": np.nan,
            "n": len(clean_data),
            "error": str(e),
            "fit_success": False
        }


def get_tto_distribution(
    df: pd.DataFrame,
    drug: Optional[str] = None,
    reaction: Optional[str] = None,
    bin_days: int = 7
) -> pd.DataFrame:
    """
    Get time-to-onset distribution histogram.
    
    Args:
        df: DataFrame with 'tto_days' column
        drug: Optional drug filter
        reaction: Optional reaction filter
        bin_days: Bin size in days (default: 7 for weekly bins)
    
    Returns:
        DataFrame with columns: bin_start, bin_end, count, cumulative_count, percentage
    """
    filtered_df = df.copy()
    
    if drug and "drug_name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["drug_name"].str.contains(drug, case=False, na=False)]
    
    if reaction and "reaction" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["reaction"].str.contains(reaction, case=False, na=False)]
    
    # Get valid TTO values
    tto_data = filtered_df["tto_days"].dropna()
    tto_data = tto_data[tto_data >= 0]
    
    if len(tto_data) == 0:
        return pd.DataFrame(columns=["bin_start", "bin_end", "count", "cumulative_count", "percentage"])
    
    # Create bins
    max_tto = int(tto_data.max())
    bins = list(range(0, max_tto + bin_days, bin_days))
    
    # Count values in each bin
    hist, bin_edges = np.histogram(tto_data, bins=bins)
    
    # Create result DataFrame
    result = pd.DataFrame({
        "bin_start": bin_edges[:-1],
        "bin_end": bin_edges[1:],
        "count": hist,
        "cumulative_count": np.cumsum(hist),
    })
    
    result["percentage"] = (result["count"] / len(tto_data) * 100).round(2)
    result["cumulative_percentage"] = (result["cumulative_count"] / len(tto_data) * 100).round(2)
    
    return result


def analyze_drug_reaction_tto(
    df: pd.DataFrame,
    drug: str,
    reaction: str
) -> Dict:
    """
    Analyze time-to-onset for a specific drug-reaction pair.
    
    Args:
        df: DataFrame with case data including 'tto_days'
        drug: Drug name
        reaction: Reaction name
    
    Returns:
        Dictionary with TTO statistics and Weibull parameters
    """
    # Filter for drug-reaction pair
    filtered = df.copy()
    
    if "drug_name" in filtered.columns:
        filtered = filtered[filtered["drug_name"].str.contains(drug, case=False, na=False)]
    
    if "reaction" in filtered.columns:
        filtered = filtered[filtered["reaction"].str.contains(reaction, case=False, na=False)]
    
    # Get TTO data
    tto_data = filtered["tto_days"].dropna() if "tto_days" in filtered.columns else pd.Series()
    tto_data = tto_data[tto_data >= 0]
    
    if len(tto_data) == 0:
        return {
            "n_cases": 0,
            "n_with_tto": 0,
            "mean_tto": np.nan,
            "median_tto": np.nan,
            "min_tto": np.nan,
            "max_tto": np.nan,
            "weibull": None
        }
    
    # Basic statistics
    stats_dict = {
        "n_cases": len(filtered),
        "n_with_tto": len(tto_data),
        "mean_tto": float(tto_data.mean()),
        "median_tto": float(tto_data.median()),
        "min_tto": float(tto_data.min()),
        "max_tto": float(tto_data.max()),
        "std_tto": float(tto_data.std()) if len(tto_data) > 1 else 0.0,
        "q25_tto": float(tto_data.quantile(0.25)),
        "q75_tto": float(tto_data.quantile(0.75)),
    }
    
    # Weibull fit
    weibull_params = fit_weibull(tto_data)
    stats_dict["weibull"] = weibull_params
    
    return stats_dict

