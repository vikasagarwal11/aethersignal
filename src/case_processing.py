"""
Case Processing Analysis for AetherSignal
Implements dechallenge/rechallenge, dose-event relationships, therapy duration,
indication analysis, and other case processing features.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.utils import parse_date, safe_divide


def analyze_dechallenge_rechallenge(df: pd.DataFrame) -> Dict:
    """
    Analyze dechallenge and rechallenge data.
    
    Dechallenge: Stopping the drug and observing if reaction improves
    Rechallenge: Restarting the drug and observing if reaction recurs
    
    Args:
        df: DataFrame with dechal and rechal columns
        
    Returns:
        Dictionary with dechallenge/rechallenge statistics
    """
    if df.empty:
        return {
            'total_cases': 0,
            'dechallenge_positive': 0,
            'dechallenge_negative': 0,
            'dechallenge_unknown': 0,
            'rechallenge_positive': 0,
            'rechallenge_negative': 0,
            'rechallenge_unknown': 0,
            'positive_dechallenge_rate': 0.0,
            'positive_rechallenge_rate': 0.0,
        }
    
    total_cases = len(df)
    
    # Dechallenge analysis
    dechal_positive = 0
    dechal_negative = 0
    dechal_unknown = 0
    
    if 'dechal' in df.columns:
        dechal_series = df['dechal'].astype(str).str.upper()
        # Y = positive (reaction improved after stopping)
        dechal_positive = dechal_series.str.contains('Y|YES|POSITIVE|1', na=False).sum()
        # N = negative (reaction did not improve)
        dechal_negative = dechal_series.str.contains('N|NO|NEGATIVE|0', na=False).sum()
        # U = unknown, or missing
        dechal_unknown = total_cases - dechal_positive - dechal_negative
    
    # Rechallenge analysis
    rechal_positive = 0
    rechal_negative = 0
    rechal_unknown = 0
    
    if 'rechal' in df.columns:
        rechal_series = df['rechal'].astype(str).str.upper()
        # Y = positive (reaction recurred after restarting)
        rechal_positive = rechal_series.str.contains('Y|YES|POSITIVE|1', na=False).sum()
        # N = negative (reaction did not recur)
        rechal_negative = rechal_series.str.contains('N|NO|NEGATIVE|0', na=False).sum()
        # U = unknown, or missing
        rechal_unknown = total_cases - rechal_positive - rechal_negative
    
    dechal_total = dechal_positive + dechal_negative
    rechal_total = rechal_positive + rechal_negative
    
    return {
        'total_cases': total_cases,
        'dechallenge_positive': int(dechal_positive),
        'dechallenge_negative': int(dechal_negative),
        'dechallenge_unknown': int(dechal_unknown),
        'rechallenge_positive': int(rechal_positive),
        'rechallenge_negative': int(rechal_negative),
        'rechallenge_unknown': int(rechal_unknown),
        'positive_dechallenge_rate': round(safe_divide(dechal_positive, dechal_total, 0.0) * 100, 2) if dechal_total > 0 else 0.0,
        'positive_rechallenge_rate': round(safe_divide(rechal_positive, rechal_total, 0.0) * 100, 2) if rechal_total > 0 else 0.0,
    }


def analyze_dose_event_relationship(df: pd.DataFrame, drug: Optional[str] = None, reaction: Optional[str] = None) -> Dict:
    """
    Analyze dose-event relationships.
    
    Args:
        df: DataFrame with dose_amt, dose_unit, dose_form columns
        drug: Optional drug filter
        reaction: Optional reaction filter
        
    Returns:
        Dictionary with dose-event statistics
    """
    filtered_df = df.copy()
    
    if drug and 'drug_name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['drug_name'].astype(str).str.contains(str(drug), case=False, na=False)]
    
    if reaction and 'reaction' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['reaction'].astype(str).str.contains(str(reaction), case=False, na=False)]
    
    if filtered_df.empty:
        return {
            'total_cases': 0,
            'cases_with_dose': 0,
            'dose_statistics': {},
            'dose_units': {},
            'dose_forms': {},
        }
    
    total_cases = len(filtered_df)
    cases_with_dose = 0
    
    # Extract dose amounts
    dose_amounts = []
    if 'dose_amt' in filtered_df.columns:
        for val in filtered_df['dose_amt'].dropna():
            try:
                # Try to extract numeric value
                val_str = str(val).strip()
                # Remove non-numeric characters except decimal point
                val_clean = ''.join(c for c in val_str if c.isdigit() or c == '.')
                if val_clean:
                    dose_amounts.append(float(val_clean))
                    cases_with_dose += 1
            except (ValueError, TypeError):
                continue
    
    dose_stats = {}
    if dose_amounts:
        dose_stats = {
            'mean': round(float(np.mean(dose_amounts)), 2),
            'median': round(float(np.median(dose_amounts)), 2),
            'min': round(float(np.min(dose_amounts)), 2),
            'max': round(float(np.max(dose_amounts)), 2),
            'std': round(float(np.std(dose_amounts)), 2) if len(dose_amounts) > 1 else 0.0,
        }
    
    # Dose units distribution
    dose_units = {}
    if 'dose_unit' in filtered_df.columns:
        dose_units = filtered_df['dose_unit'].value_counts().head(10).to_dict()
    
    # Dose forms distribution
    dose_forms = {}
    if 'dose_form' in filtered_df.columns:
        dose_forms = filtered_df['dose_form'].value_counts().head(10).to_dict()
    
    return {
        'total_cases': total_cases,
        'cases_with_dose': cases_with_dose,
        'dose_statistics': dose_stats,
        'dose_units': dose_units,
        'dose_forms': dose_forms,
    }


def analyze_therapy_duration(df: pd.DataFrame, drug: Optional[str] = None) -> Dict:
    """
    Analyze therapy duration.
    
    Args:
        df: DataFrame with start_dt, end_dt, dur, dur_cod columns
        drug: Optional drug filter
        
    Returns:
        Dictionary with therapy duration statistics
    """
    filtered_df = df.copy()
    
    if drug and 'drug_name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['drug_name'].astype(str).str.contains(str(drug), case=False, na=False)]
    
    if filtered_df.empty:
        return {
            'total_cases': 0,
            'cases_with_duration': 0,
            'duration_statistics': {},
            'duration_codes': {},
        }
    
    total_cases = len(filtered_df)
    cases_with_duration = 0
    
    # Calculate duration from dates if available
    durations_days = []
    if 'start_dt' in filtered_df.columns and 'end_dt' in filtered_df.columns:
        for idx, row in filtered_df.iterrows():
            start_date = parse_date(row.get('start_dt'))
            end_date = parse_date(row.get('end_dt'))
            if start_date and end_date:
                duration = (end_date - start_date).days
                if duration >= 0:
                    durations_days.append(duration)
                    cases_with_duration += 1
    
    # Also use dur column if available
    if 'dur' in filtered_df.columns:
        for val in filtered_df['dur'].dropna():
            try:
                val_str = str(val).strip()
                val_clean = ''.join(c for c in val_str if c.isdigit() or c == '.')
                if val_clean:
                    dur_val = float(val_clean)
                    # Assume days if value is reasonable (< 10 years)
                    if dur_val < 3650:
                        durations_days.append(dur_val)
                        cases_with_duration += 1
            except (ValueError, TypeError):
                continue
    
    duration_stats = {}
    if durations_days:
        duration_stats = {
            'mean_days': round(float(np.mean(durations_days)), 1),
            'median_days': round(float(np.median(durations_days)), 1),
            'min_days': round(float(np.min(durations_days)), 1),
            'max_days': round(float(np.max(durations_days)), 1),
            'mean_weeks': round(float(np.mean(durations_days)) / 7, 1),
            'mean_months': round(float(np.mean(durations_days)) / 30, 1),
        }
    
    # Duration codes distribution
    duration_codes = {}
    if 'dur_cod' in filtered_df.columns:
        duration_codes = filtered_df['dur_cod'].value_counts().head(10).to_dict()
    
    return {
        'total_cases': total_cases,
        'cases_with_duration': cases_with_duration,
        'duration_statistics': duration_stats,
        'duration_codes': duration_codes,
    }


def analyze_indication_vs_reaction(df: pd.DataFrame) -> Dict:
    """
    Analyze indication vs reaction relationships.
    
    Args:
        df: DataFrame with indication and reaction columns
        
    Returns:
        Dictionary with indication-reaction analysis
    """
    if df.empty or 'indication' not in df.columns or 'reaction' not in df.columns:
        return {
            'total_cases': 0,
            'cases_with_indication': 0,
            'top_indications': {},
            'indication_reaction_pairs': {},
        }
    
    total_cases = len(df)
    cases_with_indication = df['indication'].notna().sum()
    
    # Top indications
    top_indications = {}
    indication_series = df['indication'].astype(str).str.split('; ').explode()
    top_indications = indication_series.value_counts().head(10).to_dict()
    
    # Indication-reaction pairs
    indication_reaction_pairs = {}
    for idx, row in df.iterrows():
        indications = str(row.get('indication', '')).split(';')
        reactions = str(row.get('reaction', '')).split(';')
        for ind in indications:
            ind = ind.strip()
            if ind and ind.lower() != 'nan':
                for reac in reactions:
                    reac = reac.strip()
                    if reac and reac.lower() != 'nan':
                        pair = f"{ind} → {reac}"
                        indication_reaction_pairs[pair] = indication_reaction_pairs.get(pair, 0) + 1
    
    # Sort by count
    indication_reaction_pairs = dict(sorted(indication_reaction_pairs.items(), key=lambda x: x[1], reverse=True)[:20])
    
    return {
        'total_cases': total_cases,
        'cases_with_indication': int(cases_with_indication),
        'top_indications': top_indications,
        'indication_reaction_pairs': indication_reaction_pairs,
    }


def analyze_reporter_type(df: pd.DataFrame) -> Dict:
    """
    Analyze reporter type distribution.
    
    Args:
        df: DataFrame with rpsr_cod or reporter_type column
        
    Returns:
        Dictionary with reporter type statistics
    """
    if df.empty:
        return {
            'total_cases': 0,
            'reporter_types': {},
        }
    
    total_cases = len(df)
    reporter_types = {}
    
    # Check for reporter type column
    reporter_col = None
    for col in ['rpsr_cod', 'reporter_type', 'report_source', 'rpsr_code']:
        if col in df.columns:
            reporter_col = col
            break
    
    if reporter_col:
        reporter_types = df[reporter_col].value_counts().head(10).to_dict()
        # Map common FAERS codes
        code_mapping = {
            '1': 'Physician',
            '2': 'Pharmacist',
            '3': 'Other Health Professional',
            '4': 'Consumer/Non-Health Professional',
            '5': 'Lawyer',
            '6': 'Unknown',
        }
        # Replace codes with descriptions if available
        reporter_types_mapped = {}
        for code, count in reporter_types.items():
            code_str = str(code).strip()
            description = code_mapping.get(code_str, code_str)
            reporter_types_mapped[description] = count
        reporter_types = reporter_types_mapped
    
    return {
        'total_cases': total_cases,
        'reporter_types': reporter_types,
    }


def analyze_outcomes_breakdown(df: pd.DataFrame) -> Dict:
    """
    Analyze detailed outcomes breakdown (DE, HO, LT, etc.).
    
    Args:
        df: DataFrame with outcome or outc_cod column
        
    Returns:
        Dictionary with outcomes breakdown
    """
    if df.empty:
        return {
            'total_cases': 0,
            'outcomes': {},
            'outcome_codes': {},
        }
    
    total_cases = len(df)
    outcomes = {}
    outcome_codes = {}
    
    # Check for outcome column
    outcome_col = None
    for col in ['outcome', 'outc_cod', 'outcome_code']:
        if col in df.columns:
            outcome_col = col
            break
    
    if outcome_col:
        outcome_series = df[outcome_col].astype(str).str.upper()
        
        # FAERS outcome codes
        code_mapping = {
            'DE': 'Death',
            'LT': 'Life-Threatening',
            'HO': 'Hospitalization',
            'DS': 'Disability',
            'CA': 'Congenital Anomaly',
            'RI': 'Required Intervention',
            'OT': 'Other',
        }
        
        # Count outcomes
        for code, description in code_mapping.items():
            count = outcome_series.str.contains(code, na=False).sum()
            if count > 0:
                outcomes[description] = int(count)
                outcome_codes[code] = int(count)
        
        # Also count raw values
        raw_outcomes = df[outcome_col].value_counts().head(10).to_dict()
        for code, count in raw_outcomes.items():
            if str(code).upper() not in outcome_codes:
                outcome_codes[str(code).upper()] = int(count)
    
    return {
        'total_cases': total_cases,
        'outcomes': outcomes,
        'outcome_codes': outcome_codes,
    }


def detect_duplicate_cases(df: pd.DataFrame) -> Dict:
    """
    Detect duplicate cases based on case_id.
    
    Args:
        df: DataFrame with case_id, primaryid, or caseid column
        
    Returns:
        Dictionary with duplicate case information
    """
    if df.empty:
        return {
            'total_cases': 0,
            'unique_cases': 0,
            'duplicate_cases': 0,
            'duplicate_rate': 0.0,
        }
    
    # Find case ID column
    case_id_col = None
    for col in ['case_id', 'caseid', 'primaryid', 'isr', 'case']:
        if col in df.columns:
            case_id_col = col
            break
    
    if not case_id_col:
        return {
            'total_cases': len(df),
            'unique_cases': len(df),
            'duplicate_cases': 0,
            'duplicate_rate': 0.0,
        }
    
    total_cases = len(df)
    unique_cases = df[case_id_col].nunique()
    duplicate_cases = total_cases - unique_cases
    
    return {
        'total_cases': total_cases,
        'unique_cases': int(unique_cases),
        'duplicate_cases': int(duplicate_cases),
        'duplicate_rate': round(safe_divide(duplicate_cases, total_cases, 0.0) * 100, 2),
    }

