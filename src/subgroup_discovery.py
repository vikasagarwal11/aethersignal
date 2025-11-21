"""
Subgroup Discovery for AetherSignal
Automatically discovers significant subgroups (age/sex/country) for drug-event signals.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.signal_stats import calculate_prr_ror, apply_filters
from src.utils import extract_age


def discover_subgroups(
    df: pd.DataFrame,
    drug: str,
    reaction: str,
    min_cases: int = 3,
) -> Dict[str, List[Dict]]:
    """
    Discover significant subgroups (age, sex, country) for a drug-event combination.
    
    Args:
        df: Normalized DataFrame
        drug: Drug name
        reaction: Reaction name
        min_cases: Minimum cases per subgroup
        
    Returns:
        Dictionary with 'age', 'sex', 'country' subgroups, each containing
        lists of dicts with subgroup info and PRR/ROR
    """
    results = {
        'age': [],
        'sex': [],
        'country': [],
    }
    
    # Filter for this drug-event combination
    filters = {'drug': drug, 'reaction': reaction}
    filtered_df = apply_filters(df, filters)
    
    if len(filtered_df) < min_cases:
        return results
    
    # Age subgroups
    if 'age' in filtered_df.columns:
        age_groups = [
            (0, 18, 'Pediatric (0-18)'),
            (18, 30, 'Young Adult (18-30)'),
            (30, 50, 'Adult (30-50)'),
            (50, 65, 'Middle-aged (50-65)'),
            (65, 150, 'Elderly (65+)'),
        ]
        
        for age_min, age_max, label in age_groups:
            age_mask = filtered_df['age'].apply(
                lambda x: age_min <= extract_age(x) <= age_max if extract_age(x) is not None else False
            )
            age_subset = filtered_df[age_mask]
            
            if len(age_subset) >= min_cases:
                # Filter the full dataframe by age range for PRR/ROR calculation
                full_age_mask = df['age'].apply(
                    lambda x: age_min <= extract_age(x) <= age_max if extract_age(x) is not None else False
                ) if 'age' in df.columns else pd.Series([True] * len(df))
                age_filtered_df = df[full_age_mask]
                
                # Calculate PRR/ROR for drug-reaction in this age subgroup
                prr_ror = calculate_prr_ror(drug, reaction, age_filtered_df)
                if prr_ror and prr_ror.get('prr', 0) > 1.0:
                    results['age'].append({
                        'subgroup': label,
                        'age_range': f"{age_min}-{age_max}",
                        'cases': len(age_subset),
                        'prr': prr_ror.get('prr', 0),
                        'ror': prr_ror.get('ror', 0),
                    })
    
    # Sex subgroups
    if 'sex' in filtered_df.columns:
        for sex in ['M', 'F']:
            sex_mask = filtered_df['sex'].astype(str).str.upper().str.contains(sex, na=False)
            sex_subset = filtered_df[sex_mask]
            
            if len(sex_subset) >= min_cases:
                # Filter the full dataframe by sex for PRR/ROR calculation
                full_sex_mask = df['sex'].astype(str).str.upper().str.contains(sex, na=False) if 'sex' in df.columns else pd.Series([True] * len(df))
                sex_filtered_df = df[full_sex_mask]
                
                # Calculate PRR/ROR for drug-reaction in this sex subgroup
                prr_ror = calculate_prr_ror(drug, reaction, sex_filtered_df)
                if prr_ror and prr_ror.get('prr', 0) > 1.0:
                    results['sex'].append({
                        'subgroup': 'Male' if sex == 'M' else 'Female',
                        'cases': len(sex_subset),
                        'prr': prr_ror.get('prr', 0),
                        'ror': prr_ror.get('ror', 0),
                    })
    
    # Country subgroups
    if 'country' in filtered_df.columns:
        country_counts = filtered_df['country'].value_counts()
        for country, count in country_counts.items():
            if count >= min_cases and pd.notna(country):
                # Filter the full dataframe by country for PRR/ROR calculation
                full_country_mask = (df['country'].astype(str) == str(country)) if 'country' in df.columns else pd.Series([True] * len(df))
                country_filtered_df = df[full_country_mask]
                
                # Calculate PRR/ROR for drug-reaction in this country subgroup
                prr_ror = calculate_prr_ror(drug, reaction, country_filtered_df)
                if prr_ror and prr_ror.get('prr', 0) > 1.0:
                    results['country'].append({
                        'subgroup': str(country),
                        'cases': int(count),
                        'prr': prr_ror.get('prr', 0),
                        'ror': prr_ror.get('ror', 0),
                    })
    
    # Sort by PRR descending
    for key in results:
        results[key].sort(key=lambda x: x.get('prr', 0), reverse=True)
    
    return results

