"""
Signal Prioritization for AetherSignal
Implements RAG (Risk Assessment Grid) and SPS (Signal Prioritization Score).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.utils import safe_divide
from src.case_processing import analyze_dechallenge_rechallenge


def calculate_signal_prioritization_score(
    drug: str,
    reaction: str,
    df: pd.DataFrame,
    prr: Optional[float] = None,
    ror: Optional[float] = None,
    ic: Optional[float] = None,
    ebgm: Optional[float] = None,
    case_count: Optional[int] = None,
) -> Dict:
    """
    Calculate Signal Prioritization Score (SPS).
    
    Combines:
    - Statistical strength (PRR, ROR, IC, EBGM)
    - Case count
    - Seriousness
    - Dechallenge/rechallenge evidence
    - Recency
    
    Args:
        drug: Drug name
        reaction: Reaction name
        df: Filtered DataFrame for this drug-reaction pair
        prr: PRR value
        ror: ROR value
        ic: IC value
        ebgm: EBGM value
        case_count: Number of cases
        
    Returns:
        Dictionary with SPS score and components
    """
    if df.empty:
        return {
            'sps_score': 0.0,
            'sps_rank': 'Low',
            'components': {},
        }
    
    # Filter for drug-reaction pair
    filtered = df.copy()
    if 'drug_name' in filtered.columns:
        filtered = filtered[filtered['drug_name'].astype(str).str.contains(str(drug), case=False, na=False)]
    if 'reaction' in filtered.columns:
        filtered = filtered[filtered['reaction'].astype(str).str.contains(str(reaction), case=False, na=False)]
    
    if filtered.empty:
        return {
            'sps_score': 0.0,
            'sps_rank': 'Low',
            'components': {},
        }
    
    components = {}
    total_score = 0.0
    
    # 1. Statistical strength (0-30 points)
    stat_score = 0.0
    if prr and prr >= 2:
        stat_score += 10
    if ror and ror >= 2:
        stat_score += 5
    if ic and ic > 0:
        stat_score += 5
    if ebgm and ebgm >= 2:
        stat_score += 10
    components['statistical_strength'] = round(stat_score, 2)
    total_score += stat_score
    
    # 2. Case count (0-20 points)
    case_count = len(filtered) if case_count is None else case_count
    if case_count >= 100:
        case_score = 20
    elif case_count >= 50:
        case_score = 15
    elif case_count >= 20:
        case_score = 10
    elif case_count >= 10:
        case_score = 5
    else:
        case_score = 2
    components['case_count'] = round(case_score, 2)
    total_score += case_score
    
    # 3. Seriousness (0-20 points)
    serious_score = 0.0
    if 'seriousness' in filtered.columns:
        serious_count = filtered['seriousness'].apply(
            lambda x: str(x).lower() in ['1', 'yes', 'y', 'true', 'serious']
        ).sum()
        serious_rate = safe_divide(serious_count, len(filtered), 0.0)
        serious_score = serious_rate * 20
    components['seriousness'] = round(serious_score, 2)
    total_score += serious_score
    
    # 4. Dechallenge/rechallenge evidence (0-15 points)
    dechal_rechal_score = 0.0
    dechal_analysis = analyze_dechallenge_rechallenge(filtered)
    if dechal_analysis['positive_dechallenge_rate'] > 50:
        dechal_rechal_score += 5
    if dechal_analysis['positive_rechallenge_rate'] > 50:
        dechal_rechal_score += 10
    components['dechallenge_rechallenge'] = round(dechal_rechal_score, 2)
    total_score += dechal_rechal_score
    
    # 5. Recency (0-15 points)
    recency_score = 0.0
    if 'report_date' in filtered.columns or 'onset_date' in filtered.columns:
        date_col = 'report_date' if 'report_date' in filtered.columns else 'onset_date'
        dates = pd.to_datetime(filtered[date_col], errors='coerce').dropna()
        if len(dates) > 0:
            most_recent = dates.max()
            # Score based on how recent (last 6 months = 15, last year = 10, etc.)
            from datetime import datetime, timedelta
            now = datetime.now()
            days_ago = (now - most_recent.to_pydatetime()).days
            if days_ago <= 180:
                recency_score = 15
            elif days_ago <= 365:
                recency_score = 10
            elif days_ago <= 730:
                recency_score = 5
    components['recency'] = round(recency_score, 2)
    total_score += recency_score
    
    # Determine rank
    if total_score >= 70:
        rank = 'Critical'
    elif total_score >= 50:
        rank = 'High'
    elif total_score >= 30:
        rank = 'Medium'
    else:
        rank = 'Low'
    
    return {
        'sps_score': round(total_score, 2),
        'sps_rank': rank,
        'components': components,
    }


def calculate_rag_score(
    statistical_strength: float,
    clinical_seriousness: float,
) -> Dict:
    """
    Calculate Risk Assessment Grid (RAG) score.
    
    Args:
        statistical_strength: Statistical signal strength (0-100)
        clinical_seriousness: Clinical seriousness score (0-100)
        
    Returns:
        Dictionary with RAG score and quadrant
    """
    # Determine quadrant
    if statistical_strength >= 50 and clinical_seriousness >= 50:
        quadrant = 'High Risk - High Evidence'
        priority = 'Critical'
    elif statistical_strength >= 50 and clinical_seriousness < 50:
        quadrant = 'Moderate Risk - High Evidence'
        priority = 'High'
    elif statistical_strength < 50 and clinical_seriousness >= 50:
        quadrant = 'High Risk - Low Evidence'
        priority = 'High'
    else:
        quadrant = 'Low Risk - Low Evidence'
        priority = 'Medium'
    
    return {
        'rag_score': round((statistical_strength + clinical_seriousness) / 2, 2),
        'quadrant': quadrant,
        'priority': priority,
        'statistical_strength': round(statistical_strength, 2),
        'clinical_seriousness': round(clinical_seriousness, 2),
    }

