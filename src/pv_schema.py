"""
PV Schema Detection and Mapping for AetherSignal
Fuzzy column detection and mapping to standard PV fields.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
import re
from src.utils import normalize_text, map_to_meddra_pt


# Standard PV field names
STANDARD_FIELDS = {
    'case_id': ['case_id', 'caseid', 'case id', 'report_id', 'reportid', 'report id', 
                'isr', 'primaryid', 'primary id', 'unique_id', 'uniqueid'],
    'drug_name': ['drug', 'drugname', 'drug name', 'medication', 'medicinalproduct', 
                  'medicinal product', 'product', 'substance', 'drug_name', 'drugname'],
    'reaction': ['reaction', 'adverse_event', 'adverse event', 'ae', 'event', 
                 'pt', 'preferred_term', 'preferred term', 'reaction_pt', 'reactionpt',
                 'adr', 'adverse_reaction', 'adverse reaction'],
    'age': ['age', 'age_yrs', 'age_years', 'age years', 'age_yr', 'patient_age', 
            'patient age', 'age_numb', 'age_nbr'],
    'sex': ['sex', 'gender', 'patient_sex', 'patient sex', 'sex_f', 'sex_m', 
            'gndr_cod', 'gndr_cd'],
    'country': ['country', 'country_code', 'country code', 'occr_country_cd', 
                'occr_country', 'country_name', 'country name', 'country_cd'],
    'seriousness': ['serious', 'seriousness', 'serious_flg', 'serious flag', 
                    'seriousness_flag', 'seriousness flag', 'ser', 'ser_cod'],
    'onset_date': ['onset_date', 'onset date', 'event_date', 'event date', 
                   'event_dt', 'eventdt', 'onset_dt', 'onsdt', 'onset'],
    'report_date': ['report_date', 'report date', 'received_date', 'received date', 
                    'receive_date', 'receive date', 'rpt_dt', 'rptdt', 'foll_seq'],
    'outcome': ['outcome', 'outc_cod', 'outcome_code', 'outcome code', 
                'patient_outcome', 'patient outcome', 'outc'],
    # Additional case processing fields
    'dechallenge': ['dechal', 'dechallenge', 'dechallenge_code'],
    'rechallenge': ['rechal', 'rechallenge', 'rechallenge_code'],
    'dose_amount': ['dose_amt', 'dose_amount', 'dose', 'dose_amnt'],
    'dose_unit': ['dose_unit', 'dose_units', 'unit', 'dose_unit_cod'],
    'dose_form': ['dose_form', 'doseform', 'form', 'dosage_form'],
    'route': ['route', 'route_cod', 'route_code', 'route_of_admin'],
    'drug_role': ['role_cod', 'role_code', 'drug_role', 'role'],
    'therapy_start': ['start_dt', 'start_date', 'therapy_start', 'dsg_dt'],
    'therapy_end': ['end_dt', 'end_date', 'therapy_end'],
    'therapy_duration': ['dur', 'duration', 'therapy_duration'],
    'therapy_duration_code': ['dur_cod', 'duration_code', 'dur_code'],
    'indication': ['indi_pt', 'indication', 'indication_pt', 'indication_preferred_term'],
    'reporter_type': ['rpsr_cod', 'reporter_type', 'report_source', 'rpsr_code'],
}


def detect_schema(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect and map DataFrame columns to standard PV fields.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary mapping standard_field -> original_column_name
    """
    mapping = {}
    columns_lower = {col.lower(): col for col in df.columns}
    
    for standard_field, possible_names in STANDARD_FIELDS.items():
        # Try exact match first
        for name in possible_names:
            if name.lower() in columns_lower:
                mapping[standard_field] = columns_lower[name.lower()]
                break
        
        # If no exact match, try fuzzy matching
        if standard_field not in mapping:
            best_match = _fuzzy_match_column(df.columns, possible_names)
            if best_match:
                mapping[standard_field] = best_match
    
    return mapping


def _fuzzy_match_column(columns: List[str], possible_names: List[str]) -> Optional[str]:
    """
    Fuzzy match a column name against possible standard names.
    
    Args:
        columns: List of actual column names
        possible_names: List of possible standard names
        
    Returns:
        Best matching column name or None
    """
    best_match = None
    best_score = 0.0
    
    for col in columns:
        col_norm = normalize_text(col)
        for name in possible_names:
            name_norm = normalize_text(name)
            
            # Exact match
            if col_norm == name_norm:
                return col
            
            # Substring match
            if name_norm in col_norm or col_norm in name_norm:
                score = min(len(name_norm), len(col_norm)) / max(len(name_norm), len(col_norm))
                if score > best_score:
                    best_score = score
                    best_match = col
    
    # Return if score is reasonable
    if best_score > 0.5:
        return best_match
    
    return None


def normalize_dataframe(df: pd.DataFrame, schema_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Normalize DataFrame using schema mapping.
    Creates a new DataFrame with standard column names.
    Also adds MedDRA Preferred Term (PT) mapping for reactions.
    
    Args:
        df: Original DataFrame
        schema_mapping: Mapping from standard_field -> original_column
        
    Returns:
        Normalized DataFrame with standard column names and reaction_meddra column
    """
    normalized = pd.DataFrame()
    
    for standard_field, original_col in schema_mapping.items():
        if original_col in df.columns:
            normalized[standard_field] = df[original_col].copy()
        else:
            normalized[standard_field] = None
    
    # Add MedDRA Preferred Term mapping for reactions
    if 'reaction' in normalized.columns:
        normalized['reaction_meddra'] = normalized['reaction'].apply(map_to_meddra_pt)
    else:
        normalized['reaction_meddra'] = None
    
    return normalized


def get_schema_summary(schema_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Create a summary DataFrame of schema mapping for display.
    
    Args:
        schema_mapping: Mapping from standard_field -> original_column
        
    Returns:
        DataFrame with columns: 'Standard Field', 'Original Column'
    """
    summary_data = []
    for standard_field, original_col in sorted(schema_mapping.items()):
        summary_data.append({
            'Standard Field': standard_field.replace('_', ' ').title(),
            'Original Column': original_col
        })
    
    return pd.DataFrame(summary_data)


def detect_multi_value_columns(df: pd.DataFrame, schema_mapping: Dict[str, str]) -> Dict[str, bool]:
    """
    Detect if columns might contain multiple values (e.g., multiple drugs per case).
    
    Args:
        df: DataFrame
        schema_mapping: Schema mapping
        
    Returns:
        Dictionary indicating if each field might be multi-valued
    """
    multi_value = {}
    
    # Check for common multi-value patterns
    for standard_field, original_col in schema_mapping.items():
        if original_col in df.columns:
            # Check for delimiters (semicolon, pipe, comma)
            sample_values = df[original_col].dropna().astype(str).head(100)
            has_delimiters = any(
                ';' in str(val) or '|' in str(val) or 
                (',' in str(val) and len(str(val).split(',')) > 2)
                for val in sample_values
            )
            multi_value[standard_field] = has_delimiters
    
    return multi_value

