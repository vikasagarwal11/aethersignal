"""
Signal Statistics for AetherSignal
Filtering, counts, and PRR/ROR calculations with 95% CI.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from scipy import stats
from src.utils import normalize_text, parse_date, extract_age, safe_divide


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
    if filtered_df.empty:
        return filtered_df
    
    normalized_cache: Dict[str, pd.Series] = {}
    
    def get_normalized(col: str) -> Optional[pd.Series]:
        if col not in filtered_df.columns:
            return None
        if col not in normalized_cache:
            normalized_cache[col] = (
                filtered_df[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .replace("nan", "")
            )
        return normalized_cache[col]
    
    def apply_mask(mask):
        nonlocal filtered_df
        if mask is None:
            return
        if not isinstance(mask, pd.Series):
            mask = pd.Series(mask, index=filtered_df.index)
        mask = mask.fillna(False)
        filtered_df = filtered_df[mask]
        for key in normalized_cache:
            normalized_cache[key] = normalized_cache[key][mask]
    
    def build_mask(series: pd.Series, values, invert=False):
        if series is None:
            return None
        terms = values if isinstance(values, list) else [values]
        tokens = [re.escape(normalize_text(term)) for term in terms if term]
        tokens = [t for t in tokens if t]
        if not tokens:
            return None
        pattern = "|".join(tokens)
        mask = series.str.contains(pattern, na=False)
        return ~mask if invert else mask
    
    # Drug filter
    if 'drug' in filters:
        drug_series = get_normalized('drug_name')
        mask = build_mask(drug_series, filters['drug'])
        if mask is not None:
            apply_mask(mask)
    
    # Reaction filter
    if 'reaction' in filters:
        reaction_series = get_normalized('reaction')
        reaction_value = filters['reaction']
        reaction_logic = filters.get('reaction_logic', 'OR')  # Default to OR
        
        # If multiple reactions and AND logic, need to match ALL
        if isinstance(reaction_value, list) and len(reaction_value) > 1 and reaction_logic == 'AND':
            # AND logic: case must contain ALL reactions
            mask = None
            for reaction in reaction_value:
                single_mask = build_mask(reaction_series, reaction)
                if single_mask is not None:
                    mask = single_mask if mask is None else (mask & single_mask)
        else:
            # OR logic (default): case matches ANY reaction
            mask = build_mask(reaction_series, reaction_value)
        
        if mask is not None:
            apply_mask(mask)
    
    # Exclude negated reactions
    if 'exclude_reaction' in filters:
        reaction_series = get_normalized('reaction')
        mask = build_mask(reaction_series, filters['exclude_reaction'], invert=True)
        if mask is not None:
            apply_mask(mask)
    
    # Age filter
    if ('age_min' in filters or 'age_max' in filters) and 'age' in filtered_df.columns:
        age_values = filtered_df['age'].apply(extract_age)
        if 'age_min' in filters:
            apply_mask(age_values >= filters['age_min'])
        if 'age_max' in filters:
            apply_mask(age_values <= filters['age_max'])
    
    # Sex filter
    if 'sex' in filters:
        sex_series = get_normalized('sex')
        if sex_series is not None:
            target = normalize_text(filters['sex'])
            mask = sex_series == target
            apply_mask(mask)
    
    # Country filter
    if 'country' in filters:
        country_series = get_normalized('country')
        if country_series is not None:
            target = normalize_text(filters['country'])
            mask = country_series.str.contains(re.escape(target), na=False)
            apply_mask(mask)
    
    # Seriousness filter
    if filters.get('seriousness') and 'seriousness' in filtered_df.columns:
        serious_series = get_normalized('seriousness')
        if serious_series is not None:
            allowed = {'1', 'yes', 'y', 'true', 'serious'}
            mask = serious_series.isin(allowed)
            apply_mask(mask)
    
    # Date filters
    if 'onset_date' in filtered_df.columns and ('date_from' in filters or 'date_to' in filters):
        date_values = pd.to_datetime(filtered_df['onset_date'], errors='coerce')
        if 'date_from' in filters:
            date_from = parse_date(filters['date_from'])
            if date_from:
                apply_mask(date_values >= date_from)
        if 'date_to' in filters:
            date_to = parse_date(filters['date_to'])
            if date_to:
                apply_mask(date_values <= date_to)
    
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


def get_data_quality_metrics(df: pd.DataFrame) -> Dict:
    """
    Compute basic data quality metrics for the normalized dataset.
    """
    if df is None or df.empty:
        return {
            'row_count': 0,
            'column_count': 0,
            'missing_percent': {},
            'duplicate_cases': 0,
            'quality_score': 0,
            'quality_color': 'red',
            'quality_label': 'Poor',
        }
    
    key_fields = [
        'case_id', 'drug_name', 'reaction', 'age', 'sex',
        'country', 'seriousness', 'onset_date', 'report_date'
    ]
    missing_percent = {}
    for field in key_fields:
        if field in df.columns:
            missing_percent[field] = round(float(df[field].isna().mean() * 100), 2)
    
    duplicate_cases = 0
    if 'case_id' in df.columns:
        duplicate_cases = int(df['case_id'].duplicated().sum())
    
    # Calculate quality score (0-100)
    # Weight: completeness (50%), uniqueness (30%), schema coverage (20%)
    total_rows = len(df)
    
    # Completeness score (0-50 points)
    # Average completeness across key fields
    completeness_scores = []
    for field in key_fields:
        if field in df.columns:
            completeness = 100 - missing_percent.get(field, 100)
            completeness_scores.append(completeness)
    
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
    completeness_points = (avg_completeness / 100) * 50
    
    # Uniqueness score (0-30 points)
    # Penalize duplicates
    duplicate_rate = (duplicate_cases / total_rows * 100) if total_rows > 0 else 0
    uniqueness_points = max(0, 30 - (duplicate_rate / 100) * 30)
    
    # Schema coverage score (0-20 points)
    # How many key fields are present
    fields_present = sum(1 for field in key_fields if field in df.columns)
    schema_points = (fields_present / len(key_fields)) * 20
    
    quality_score = round(completeness_points + uniqueness_points + schema_points, 1)
    quality_score = max(0, min(100, quality_score))  # Clamp to 0-100
    
    # Determine color and label
    if quality_score >= 80:
        quality_color = 'green'
        quality_label = 'Excellent'
    elif quality_score >= 60:
        quality_color = 'yellow'
        quality_label = 'Good'
    elif quality_score >= 40:
        quality_color = 'orange'
        quality_label = 'Fair'
    else:
        quality_color = 'red'
        quality_label = 'Poor'
    
    return {
        'row_count': len(df),
        'column_count': len(df.columns),
        'missing_percent': missing_percent,
        'duplicate_cases': duplicate_cases,
        'quality_score': quality_score,
        'quality_color': quality_color,
        'quality_label': quality_label,
    }


def describe_signal(prr_ror: Dict) -> str:
    """
    Provide a natural language explanation of PRR/ROR results.
    """
    if not prr_ror:
        return ""
    a = prr_ror.get('a', 0)
    b = prr_ror.get('b', 0)
    c = prr_ror.get('c', 0)
    d = prr_ror.get('d', 0)
    prr = prr_ror.get('prr', 0)
    ror = prr_ror.get('ror', 0)
    seriousness_hint = ""
    if prr >= 2 and ror >= 2:
        seriousness_hint = "This combination meets typical disproportionality thresholds (PRR/ROR ≥ 2)."
    elif prr >= 1.5 or ror >= 1.5:
        seriousness_hint = "Signals are elevated but below the usual PRR/ROR=2 threshold."
    else:
        seriousness_hint = "Disproportionality metrics are modest; interpret with caution."
    return (
        f"{a} cases report both the drug and reaction, with {b} additional reports for the drug alone "
        f"and {c} reports for the reaction with other drugs. PRR={prr:.2f}, ROR={ror:.2f}. "
        f"{seriousness_hint}"
    )

