"""
New signal detection (unexpectedness scoring) for AetherSignal.
Identifies novel or unexpected drug-reaction signals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from collections import Counter

from src import signal_stats
from src.utils import normalize_text, safe_divide


def calculate_unexpectedness_score(
    drug: str,
    reaction: str,
    normalized_df: pd.DataFrame,
    historical_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Calculate unexpectedness score for a drug-reaction pair.
    
    Higher score = more unexpected/novel signal.
    
    Args:
        drug: Drug name
        reaction: Reaction name
        normalized_df: Current dataset
        historical_df: Optional historical dataset for comparison
        
    Returns:
        Dictionary with unexpectedness metrics
    """
    # Filter for drug-reaction pair
    drug_mask = normalized_df["drug_name"].apply(
        lambda x: normalize_text(str(drug)) in normalize_text(str(x))
    )
    reaction_mask = normalized_df["reaction"].apply(
        lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
    )
    
    pair_cases = normalized_df[drug_mask & reaction_mask]
    n_pair = len(pair_cases)
    
    if n_pair == 0:
        return {
            "unexpectedness_score": 0.0,
            "novelty_score": 0.0,
            "frequency_score": 0.0,
            "rarity_score": 0.0,
            "is_novel": False,
            "is_rare": False,
            "explanation": "No cases found for this drug-reaction pair"
        }
    
    # 1. Novelty: Is this a new combination?
    # Check if drug-reaction pair exists in historical data
    novelty_score = 1.0  # Default: assume novel
    is_novel = True
    
    if historical_df is not None and len(historical_df) > 0:
        hist_drug_mask = historical_df["drug_name"].apply(
            lambda x: normalize_text(str(drug)) in normalize_text(str(x))
        )
        hist_reaction_mask = historical_df["reaction"].apply(
            lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
        )
        hist_pair_cases = historical_df[hist_drug_mask & hist_reaction_mask]
        
        if len(hist_pair_cases) > 0:
            is_novel = False
            novelty_score = 0.0
        else:
            # Check if reaction is known for this drug class
            novelty_score = 0.5  # Partially novel
    
    # 2. Frequency: How common is this reaction for this drug?
    drug_cases = normalized_df[drug_mask]
    n_drug_total = len(drug_cases)
    
    reaction_cases = normalized_df[reaction_mask]
    n_reaction_total = len(reaction_cases)
    
    # Expected frequency if independent
    expected_freq = safe_divide(n_drug_total * n_reaction_total, len(normalized_df), 0.0)
    observed_freq = n_pair
    
    # Frequency ratio
    freq_ratio = safe_divide(observed_freq, expected_freq, 0.0) if expected_freq > 0 else 0.0
    
    # Frequency score: inverse of how expected this is
    # If freq_ratio is very high, it's expected (low unexpectedness)
    # If freq_ratio is very low, it's unexpected (high unexpectedness)
    frequency_score = 1.0 / (1.0 + freq_ratio) if freq_ratio > 0 else 1.0
    
    # 3. Rarity: How rare is this reaction overall?
    total_cases = len(normalized_df)
    reaction_prevalence = safe_divide(n_reaction_total, total_cases, 0.0)
    
    # Rarity score: higher for rarer reactions
    rarity_score = 1.0 - reaction_prevalence  # Inverse of prevalence
    
    # 4. Drug-reaction co-occurrence pattern
    # Check if this reaction appears with other drugs in similar patterns
    drug_reaction_counts = Counter()
    for _, row in normalized_df.iterrows():
        drugs = str(row.get("drug_name", "")).split(";")
        reactions = str(row.get("reaction", "")).split(";")
        for d in drugs:
            for r in reactions:
                if d.strip() and r.strip():
                    drug_reaction_counts[(normalize_text(d.strip()), normalize_text(r.strip()))] += 1
    
    # How many other drugs show this reaction?
    other_drugs_with_reaction = sum(
        1 for (d, r), count in drug_reaction_counts.items()
        if normalize_text(r) == normalize_text(reaction) and normalize_text(d) != normalize_text(drug) and count >= 3
    )
    
    # Pattern score: if many other drugs show this reaction, it's less unexpected
    pattern_score = 1.0 / (1.0 + other_drugs_with_reaction * 0.1) if other_drugs_with_reaction > 0 else 1.0
    
    # Combined unexpectedness score (0-100)
    unexpectedness_score = (
        novelty_score * 40 +  # 40% weight on novelty
        frequency_score * 30 +  # 30% weight on frequency
        rarity_score * 20 +  # 20% weight on rarity
        pattern_score * 10  # 10% weight on pattern
    ) * 100
    
    # Thresholds
    is_rare = reaction_prevalence < 0.01  # Less than 1% of all cases
    
    # Explanation
    explanation_parts = []
    if is_novel:
        explanation_parts.append("Novel drug-reaction combination")
    if is_rare:
        explanation_parts.append("Rare reaction")
    if freq_ratio < 0.5:
        explanation_parts.append("Lower than expected frequency")
    if other_drugs_with_reaction == 0:
        explanation_parts.append("Unique to this drug")
    
    explanation = "; ".join(explanation_parts) if explanation_parts else "Expected signal pattern"
    
    return {
        "unexpectedness_score": float(unexpectedness_score),
        "novelty_score": float(novelty_score * 100),
        "frequency_score": float(frequency_score * 100),
        "rarity_score": float(rarity_score * 100),
        "pattern_score": float(pattern_score * 100),
        "is_novel": is_novel,
        "is_rare": is_rare,
        "n_cases": n_pair,
        "expected_freq": float(expected_freq),
        "observed_freq": float(observed_freq),
        "freq_ratio": float(freq_ratio),
        "reaction_prevalence": float(reaction_prevalence),
        "other_drugs_with_reaction": other_drugs_with_reaction,
        "explanation": explanation,
    }


def detect_new_signals(
    normalized_df: pd.DataFrame,
    min_cases: int = 3,
    unexpectedness_threshold: float = 60.0,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Detect new/unexpected signals across all drug-reaction pairs.
    
    Args:
        normalized_df: Normalized dataset
        min_cases: Minimum cases required
        unexpectedness_threshold: Minimum unexpectedness score
        top_n: Maximum number of signals to return
        
    Returns:
        DataFrame with new signals sorted by unexpectedness score
    """
    # Get all unique drug-reaction pairs
    drug_reaction_pairs = set()
    
    for _, row in normalized_df.iterrows():
        drugs = str(row.get("drug_name", "")).split(";")
        reactions = str(row.get("reaction", "")).split(";")
        for d in drugs:
            for r in reactions:
                if d.strip() and r.strip():
                    drug_reaction_pairs.add((d.strip(), r.strip()))
    
    # Calculate unexpectedness for each pair
    new_signals = []
    
    for drug, reaction in drug_reaction_pairs:
        # Count cases
        drug_mask = normalized_df["drug_name"].apply(
            lambda x: normalize_text(str(drug)) in normalize_text(str(x))
        )
        reaction_mask = normalized_df["reaction"].apply(
            lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
        )
        n_cases = (drug_mask & reaction_mask).sum()
        
        if n_cases >= min_cases:
            unexpectedness = calculate_unexpectedness_score(drug, reaction, normalized_df)
            
            if unexpectedness["unexpectedness_score"] >= unexpectedness_threshold:
                new_signals.append({
                    "drug": drug,
                    "reaction": reaction,
                    "n_cases": n_cases,
                    "unexpectedness_score": unexpectedness["unexpectedness_score"],
                    "novelty_score": unexpectedness["novelty_score"],
                    "frequency_score": unexpectedness["frequency_score"],
                    "rarity_score": unexpectedness["rarity_score"],
                    "is_novel": unexpectedness["is_novel"],
                    "is_rare": unexpectedness["is_rare"],
                    "explanation": unexpectedness["explanation"],
                })
    
    if not new_signals:
        return pd.DataFrame()
    
    # Convert to DataFrame and sort
    signals_df = pd.DataFrame(new_signals)
    signals_df = signals_df.sort_values("unexpectedness_score", ascending=False).head(top_n)
    
    return signals_df

