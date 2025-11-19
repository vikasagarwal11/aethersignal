"""
Signal Statistics for AetherSignal
Filtering, counts, and PRR/ROR calculations with 95% CI.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from utils import normalize_text, parse_date, extract_age, safe_divide


def apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """
    Apply filters to DataFrame.
    
    Args:
        df: Normalized DataFrame with standard column names
        filters: Filter dictionary from nl_query_parser (may include 'exclude_reaction')
        
    Returns:
        Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # Drug filter
    if 'drug' in filters and 'drug_name' in filtered_df.columns:
        drug_filter = filters['drug']
        if isinstance(drug_filter, list):
            mask = filtered_df['drug_name'].apply(
                lambda x: any(normalize_text(d) in normalize_text(str(x)) for d in drug_filter)
            )
        else:
            mask = filtered_df['drug_name'].apply(
                lambda x: normalize_text(drug_filter) in normalize_text(str(x))
            )
        filtered_df = filtered_df[mask]
    
    # Reaction filter
    if 'reaction' in filters and 'reaction' in filtered_df.columns:
        reaction_filter = filters['reaction']
        if isinstance(reaction_filter, list):
            mask = filtered_df['reaction'].apply(
                lambda x: any(normalize_text(r) in normalize_text(str(x)) for r in reaction_filter)
            )
        else:
            mask = filtered_df['reaction'].apply(
                lambda x: normalize_text(reaction_filter) in normalize_text(str(x))
            )
        filtered_df = filtered_df[mask]
    
    # Exclude negated reactions
    if 'exclude_reaction' in filters and 'reaction' in filtered_df.columns:
        exclude_list = filters['exclude_reaction']
        if isinstance(exclude_list, list):
            # Exclude any reaction that contains any of the excluded terms
            exclude_mask = filtered_df['reaction'].apply(
                lambda x: not any(
                    normalize_text(ex) in normalize_text(str(x)) 
                    for ex in exclude_list
                )
            )
        else:
            # Single exclusion term
            exclude_mask = filtered_df['reaction'].apply(
                lambda x: normalize_text(exclude_list) not in normalize_text(str(x))
            )
        filtered_df = filtered_df[exclude_mask]
    
    # Age filter
    if ('age_min' in filters or 'age_max' in filters) and 'age' in filtered_df.columns:
        age_values = filtered_df['age'].apply(extract_age)
        if 'age_min' in filters:
            filtered_df = filtered_df[age_values >= filters['age_min']]
        if 'age_max' in filters:
            filtered_df = filtered_df[age_values <= filters['age_max']]
    
    # Sex filter
    if 'sex' in filters and 'sex' in filtered_df.columns:
        sex_filter = normalize_text(filters['sex'])
        mask = filtered_df['sex'].apply(lambda x: normalize_text(str(x)) == sex_filter)
        filtered_df = filtered_df[mask]
    
    # Country filter
    if 'country' in filters and 'country' in filtered_df.columns:
        country_filter = normalize_text(filters['country'])
        mask = filtered_df['country'].apply(
            lambda x: normalize_text(str(x)) == country_filter or 
                     country_filter in normalize_text(str(x))
        )
        filtered_df = filtered_df[mask]
    
    # Seriousness filter
    if 'seriousness' in filters and filters['seriousness'] and 'seriousness' in filtered_df.columns:
        mask = filtered_df['seriousness'].apply(
            lambda x: normalize_text(str(x)) in ['1', 'yes', 'y', 'true', 'serious']
        )
        filtered_df = filtered_df[mask]
    
    # Date filters
    if 'date_from' in filters and 'onset_date' in filtered_df.columns:
        date_from = parse_date(filters['date_from'])
        if date_from:
            date_values = filtered_df['onset_date'].apply(parse_date)
            filtered_df = filtered_df[date_values >= date_from]
    
    if 'date_to' in filters and 'onset_date' in filtered_df.columns:
        date_to = parse_date(filters['date_to'])
        if date_to:
            date_values = filtered_df['onset_date'].apply(parse_date)
            filtered_df = filtered_df[date_values <= date_to]
    
    return filtered_df


def calculate_prr_ror(drug: str, reaction: str, df: pd.DataFrame) -> Optional[Dict]:
    """
    Calculate Proportional Reporting Ratio (PRR) and Reporting Odds Ratio (ROR)
    with 95% confidence intervals.
    
    Creates a 2x2 contingency table:
        | Reaction | No Reaction
    Drug|    a     |     b
    No  |    c     |     d
    
    Args:
        drug: Drug name
        reaction: Reaction name
        df: Normalized DataFrame
        
    Returns:
        Dictionary with PRR, ROR, and 95% CI, or None if calculation not possible
    """
    # Check if required columns exist
    if 'drug_name' not in df.columns or 'reaction' not in df.columns:
        return None
    
    # Create binary indicators
    drug_mask = df['drug_name'].apply(
        lambda x: normalize_text(drug) in normalize_text(str(x))
    )
    reaction_mask = df['reaction'].apply(
        lambda x: normalize_text(reaction) in normalize_text(str(x))
    )
    
    # Build 2x2 table
    a = ((drug_mask) & (reaction_mask)).sum()  # Drug + Reaction
    b = ((drug_mask) & (~reaction_mask)).sum()  # Drug, no Reaction
    c = ((~drug_mask) & (reaction_mask)).sum()  # No Drug, Reaction
    d = ((~drug_mask) & (~reaction_mask)).sum()  # No Drug, no Reaction
    
    # Check if we can calculate
    if a == 0 or (b == 0 and c == 0) or (a + b == 0) or (a + c == 0):
        return None
    
    # Calculate PRR
    prr = safe_divide(a * (c + d), c * (a + b))
    
    # Calculate PRR 95% CI (log-normal approximation)
    if prr > 0:
        log_prr = np.log(prr)
        se_log_prr = np.sqrt(1/a + 1/b + 1/c + 1/d)
        prr_ci_lower = np.exp(log_prr - 1.96 * se_log_prr)
        prr_ci_upper = np.exp(log_prr + 1.96 * se_log_prr)
    else:
        prr_ci_lower = prr_ci_upper = 0.0
    
    # Calculate ROR
    ror = safe_divide(a * d, b * c)
    
    # Calculate ROR 95% CI (log-normal approximation)
    if ror > 0:
        log_ror = np.log(ror)
        se_log_ror = np.sqrt(1/a + 1/b + 1/c + 1/d)
        ror_ci_lower = np.exp(log_ror - 1.96 * se_log_ror)
        ror_ci_upper = np.exp(log_ror + 1.96 * se_log_ror)
    else:
        ror_ci_lower = ror_ci_upper = 0.0
    
    # Chi-square test
    contingency_table = np.array([[a, b], [c, d]])
    try:
        chi2, p_value = stats.chi2_contingency(contingency_table)[:2]
    except:
        chi2, p_value = None, None
    
    return {
        'drug': drug,
        'reaction': reaction,
        'a': int(a),
        'b': int(b),
        'c': int(c),
        'd': int(d),
        'prr': prr,
        'prr_ci_lower': prr_ci_lower,
        'prr_ci_upper': prr_ci_upper,
        'ror': ror,
        'ror_ci_lower': ror_ci_lower,
        'ror_ci_upper': ror_ci_upper,
        'chi2': chi2,
        'p_value': p_value,
    }


def get_summary_stats(filtered_df: pd.DataFrame, total_df: pd.DataFrame) -> Dict:
    """
    Calculate summary statistics for filtered data.
    
    Args:
        filtered_df: Filtered DataFrame
        total_df: Total/complete DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    total_cases = len(total_df)
    matching_cases = len(filtered_df)
    percentage = safe_divide(matching_cases, total_cases, 0.0) * 100
    
    # Top drugs
    top_drugs = {}
    if 'drug_name' in filtered_df.columns:
        top_drugs = filtered_df['drug_name'].value_counts().head(10).to_dict()
    
    # Top reactions
    top_reactions = {}
    if 'reaction' in filtered_df.columns:
        top_reactions = filtered_df['reaction'].value_counts().head(10).to_dict()
    
    # Age statistics
    age_stats = {}
    if 'age' in filtered_df.columns:
        ages = filtered_df['age'].apply(extract_age).dropna()
        age_stats = {
            'mean': float(ages.mean()) if len(ages) > 0 else None,
            'median': float(ages.median()) if len(ages) > 0 else None,
            'min': float(ages.min()) if len(ages) > 0 else None,
            'max': float(ages.max()) if len(ages) > 0 else None,
        }
    
    # Sex distribution
    sex_dist = {}
    if 'sex' in filtered_df.columns:
        sex_dist = filtered_df['sex'].value_counts().to_dict()
    
    # Country distribution
    country_dist = {}
    if 'country' in filtered_df.columns:
        country_dist = filtered_df['country'].value_counts().head(10).to_dict()
    
    # Seriousness
    serious_count = 0
    if 'seriousness' in filtered_df.columns:
        serious_count = filtered_df['seriousness'].apply(
            lambda x: normalize_text(str(x)) in ['1', 'yes', 'y', 'true', 'serious']
        ).sum()
    
    # Time trend (if dates available)
    time_trend = None
    if 'onset_date' in filtered_df.columns:
        date_values = filtered_df['onset_date'].apply(parse_date).dropna()
        if len(date_values) > 0:
            date_values = pd.Series(date_values)
            time_trend = date_values.groupby(date_values.dt.to_period('M')).size().to_dict()
            # Convert Period objects to strings
            time_trend = {str(k): int(v) for k, v in time_trend.items()}
    
    return {
        'total_cases': total_cases,
        'matching_cases': matching_cases,
        'percentage': percentage,
        'top_drugs': top_drugs,
        'top_reactions': top_reactions,
        'age_stats': age_stats,
        'sex_distribution': sex_dist,
        'country_distribution': country_dist,
        'serious_count': int(serious_count),
        'serious_percentage': safe_divide(serious_count, matching_cases, 0.0) * 100,
        'time_trend': time_trend,
    }


def get_top_co_reactions(filtered_df: pd.DataFrame, reaction: Optional[str] = None, top_n: int = 10) -> List[Dict]:
    """
    Get top co-occurring reactions.
    
    Args:
        filtered_df: Filtered DataFrame
        reaction: Optional reaction to exclude from results
        top_n: Number of top reactions to return
        
    Returns:
        List of dictionaries with reaction and count
    """
    if 'reaction' not in filtered_df.columns:
        return []
    
    if reaction:
        reaction_norm = normalize_text(reaction)
        co_reactions = filtered_df['reaction'].apply(
            lambda x: normalize_text(str(x)) != reaction_norm
        )
        reaction_counts = filtered_df[co_reactions]['reaction'].value_counts()
    else:
        reaction_counts = filtered_df['reaction'].value_counts()
    
    return [
        {'reaction': reaction, 'count': int(count)}
        for reaction, count in reaction_counts.head(top_n).items()
    ]


def get_drug_event_combinations(df: pd.DataFrame, min_cases: int = 3) -> List[Dict]:
    """
    Get all drug-event combinations with minimum case count.
    
    Args:
        df: Normalized DataFrame
        min_cases: Minimum number of cases for a combination
        
    Returns:
        List of dictionaries with drug, reaction, and count
    """
    if 'drug_name' not in df.columns or 'reaction' not in df.columns:
        return []
    
    combinations = df.groupby(['drug_name', 'reaction']).size().reset_index(name='count')
    combinations = combinations[combinations['count'] >= min_cases]
    combinations = combinations.sort_values('count', ascending=False)
    
    return [
        {
            'drug': row['drug_name'],
            'reaction': row['reaction'],
            'count': int(row['count'])
        }
        for _, row in combinations.iterrows()
    ]

