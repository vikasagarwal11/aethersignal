"""
Exposure normalization for AetherSignal.
Adjusts signal detection metrics for drug exposure rates (prescriptions/patients).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from src import signal_stats
from src.utils import safe_divide


def normalize_by_exposure(
    drug: str,
    reaction: str,
    normalized_df: pd.DataFrame,
    exposure_data: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Normalize signal metrics by drug exposure (prescriptions/patients).
    
    Args:
        drug: Drug name
        reaction: Reaction name
        normalized_df: Normalized dataset
        exposure_data: Optional dictionary mapping drug names to exposure counts
                      If None, uses case counts as proxy
        
    Returns:
        Dictionary with exposure-normalized metrics
    """
    # Get case counts
    drug_mask = normalized_df["drug_name"].apply(
        lambda x: str(drug).lower() in str(x).lower()
    )
    reaction_mask = normalized_df["reaction"].apply(
        lambda x: str(reaction).lower() in str(x).lower()
    )
    
    a = (drug_mask & reaction_mask).sum()
    b = (drug_mask & ~reaction_mask).sum()
    c = (~drug_mask & reaction_mask).sum()
    d = (~drug_mask & ~reaction_mask).sum()
    
    # Get exposure counts
    if exposure_data:
        drug_exposure = exposure_data.get(drug, 0.0)
        total_exposure = sum(exposure_data.values())
    else:
        # Use case counts as proxy (assuming each case = 1 exposure)
        drug_exposure = float(a + b)  # All cases with this drug
        total_exposure = float(len(normalized_df))
    
    if drug_exposure == 0:
        return {
            "exposure_adjusted_rate": 0.0,
            "crude_rate": 0.0,
            "exposure_ratio": 0.0,
            "normalized_prr": 0.0,
            "exposure_per_million": 0.0,
            "cases_per_million_exposures": 0.0,
        }
    
    # Crude reporting rate (cases per exposure)
    crude_rate = safe_divide(a, drug_exposure, 0.0)
    
    # Exposure-adjusted rate (per million exposures)
    exposure_per_million = safe_divide(drug_exposure, total_exposure, 0.0) * 1_000_000
    cases_per_million_exposures = safe_divide(a, drug_exposure, 0.0) * 1_000_000
    
    # Background rate (reaction in non-drug cases)
    non_drug_exposure = total_exposure - drug_exposure
    background_rate = safe_divide(c, non_drug_exposure, 0.0) if non_drug_exposure > 0 else 0.0
    
    # Exposure ratio (drug exposure / total exposure)
    exposure_ratio = safe_divide(drug_exposure, total_exposure, 0.0)
    
    # Normalized PRR (adjusted for exposure)
    if background_rate > 0:
        normalized_prr = safe_divide(crude_rate, background_rate, 0.0)
    else:
        normalized_prr = 0.0
    
    # Standard PRR for comparison
    prr_result = signal_stats.calculate_prr_ror(a, b, c, d)
    crude_prr = prr_result.get("prr", 0.0)
    
    return {
        "exposure_adjusted_rate": float(crude_rate),
        "crude_rate": float(crude_rate),
        "exposure_ratio": float(exposure_ratio),
        "normalized_prr": float(normalized_prr),
        "crude_prr": float(crude_prr),
        "exposure_per_million": float(exposure_per_million),
        "cases_per_million_exposures": float(cases_per_million_exposures),
        "background_rate": float(background_rate),
        "drug_exposure": float(drug_exposure),
        "total_exposure": float(total_exposure),
    }


def calculate_incidence_rate(
    drug: str,
    normalized_df: pd.DataFrame,
    exposure_data: Optional[Dict[str, float]] = None,
    time_period_days: float = 365.0
) -> Dict:
    """
    Calculate incidence rate (cases per person-year of exposure).
    
    Args:
        drug: Drug name
        normalized_df: Normalized dataset
        exposure_data: Optional exposure data
        time_period_days: Time period in days (default: 1 year)
        
    Returns:
        Dictionary with incidence rate metrics
    """
    drug_mask = normalized_df["drug_name"].apply(
        lambda x: str(drug).lower() in str(x).lower()
    )
    drug_cases = normalized_df[drug_mask]
    n_cases = len(drug_cases)
    
    if exposure_data:
        drug_exposure = exposure_data.get(drug, 0.0)
    else:
        drug_exposure = float(n_cases)  # Proxy
    
    if drug_exposure == 0:
        return {
            "incidence_rate": 0.0,
            "incidence_rate_per_1000": 0.0,
            "person_years": 0.0,
        }
    
    # Person-years of exposure (assuming average exposure duration)
    # If we have therapy duration data, use it; otherwise assume average
    if "dur" in drug_cases.columns:
        avg_duration_days = drug_cases["dur"].dropna().mean()
        if pd.isna(avg_duration_days) or avg_duration_days == 0:
            avg_duration_days = time_period_days  # Default to 1 year
    else:
        avg_duration_days = time_period_days
    
    person_years = safe_divide(drug_exposure * avg_duration_days, time_period_days, 0.0)
    
    # Incidence rate (cases per person-year)
    incidence_rate = safe_divide(n_cases, person_years, 0.0)
    incidence_rate_per_1000 = incidence_rate * 1000
    
    return {
        "incidence_rate": float(incidence_rate),
        "incidence_rate_per_1000": float(incidence_rate_per_1000),
        "person_years": float(person_years),
        "n_cases": n_cases,
        "drug_exposure": float(drug_exposure),
        "avg_duration_days": float(avg_duration_days),
    }


def compare_exposure_adjusted_signals(
    normalized_df: pd.DataFrame,
    drug_reaction_pairs: List[tuple],
    exposure_data: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Compare multiple drug-reaction signals adjusted for exposure.
    
    Args:
        normalized_df: Normalized dataset
        drug_reaction_pairs: List of (drug, reaction) tuples
        exposure_data: Optional exposure data
        
    Returns:
        DataFrame with exposure-adjusted metrics for each pair
    """
    results = []
    
    for drug, reaction in drug_reaction_pairs:
        normalized = normalize_by_exposure(drug, reaction, normalized_df, exposure_data)
        results.append({
            "drug": drug,
            "reaction": reaction,
            "cases_per_million_exposures": normalized["cases_per_million_exposures"],
            "exposure_adjusted_rate": normalized["exposure_adjusted_rate"],
            "normalized_prr": normalized["normalized_prr"],
            "crude_prr": normalized["crude_prr"],
        })
    
    return pd.DataFrame(results).sort_values("cases_per_million_exposures", ascending=False)

