"""
Integration module for merging Social AE data with FAERS data.
Handles normalization and merging for Quantum ranking.
"""

import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

from .social_storage import load_recent_social
from .social_ae_storage import get_posts as get_posts_sqlite
from .social_ae_supabase import normalize_social_ae_to_faers


def load_social_ae_data(
    days_back: int = 30,
    use_supabase: bool = True,
    drug_filter: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Load Social AE data and normalize to FAERS structure.
    
    Args:
        days_back: Days back to load
        use_supabase: Use Supabase (True) or SQLite (False)
        drug_filter: Optional drug name filter
    
    Returns:
        Normalized DataFrame compatible with FAERS structure, or None
    """
    try:
        if use_supabase:
            df = load_recent_social(days=days_back)
            if not df.empty and drug_filter:
                df = df[df["drug_name"].str.contains(drug_filter, case=False, na=False)]
        else:
            df = get_posts_sqlite(
                drug_match=drug_filter,
                days_back=days_back,
                limit=5000
            )
        
        if df.empty:
            return None
        
        # Normalize to FAERS structure
        df_normalized = normalize_social_ae_to_faers(df)
        
        return df_normalized
        
    except Exception:
        return None


def merge_faers_and_social_ae(
    faers_df: pd.DataFrame,
    social_ae_df: Optional[pd.DataFrame],
    social_weight: float = 0.4
) -> pd.DataFrame:
    """
    Merge FAERS and Social AE data for unified analysis.
    
    Args:
        faers_df: FAERS normalized DataFrame
        social_ae_df: Social AE normalized DataFrame (or None)
        social_weight: Weight for social signals (0.0-1.0)
    
    Returns:
        Merged DataFrame
    """
    if social_ae_df is None or social_ae_df.empty:
        return faers_df
    
    # Mark data sources
    faers_df = faers_df.copy()
    faers_df["data_source"] = "faers"
    faers_df["social_weight"] = 1.0  # Full weight for FAERS
    
    social_ae_df = social_ae_df.copy()
    social_ae_df["data_source"] = "social_ae"
    social_ae_df["social_weight"] = social_weight  # Reduced weight for social
    
    # Merge
    merged = pd.concat([faers_df, social_ae_df], ignore_index=True)
    
    return merged


def enhance_quantum_scores_with_social(
    combos: list,
    social_ae_df: Optional[pd.DataFrame],
    social_weight: float = 0.4
) -> list:
    """
    Enhance quantum scores with social AE signals.
    
    Args:
        combos: List of drug-event combination dictionaries
        social_ae_df: Social AE DataFrame
        social_weight: Weight for social signals
    
    Returns:
        Enhanced combos with social_count and boosted quantum_score
    """
    if social_ae_df is None or social_ae_df.empty:
        return combos
    
    # Count social AE signals per drug-event pair
    social_counts = {}
    if "drug_name" in social_ae_df.columns and "reaction" in social_ae_df.columns:
        social_grouped = social_ae_df.groupby(["drug_name", "reaction"]).size()
        for (drug, reaction), count in social_grouped.items():
            key = f"{drug}|{reaction}"
            social_counts[key] = int(count)
    
    # Enhance each combo
    for combo in combos:
        drug = combo.get("drug", "")
        reaction = combo.get("reaction", "")
        key = f"{drug}|{reaction}"
        
        social_count = social_counts.get(key, 0)
        combo["social_count"] = social_count
        
        # Boost quantum score with social signals
        if social_count > 0:
            base_score = combo.get("quantum_score", 0.0)
            social_boost = social_weight * min(social_count / 10.0, 1.0)  # Cap at 1.0
            combo["quantum_score"] = base_score + (social_boost * 0.2)  # 20% boost max
    
    return combos

