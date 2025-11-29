"""
Query auto-correction and suggestion helpers.
Uses rapidfuzz to suggest fixes for drug/reaction typos and keyword fallbacks.
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process


def _unique_strings(series: pd.Series, top_n: int = 5000) -> List[str]:
    """Return a truncated list of unique, non-empty strings for matching."""
    vals = (
        series.dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .replace("", pd.NA)
        .dropna()
    )
    return vals.unique().tolist()[:top_n]


# Cache for candidates to avoid repeated processing
_candidates_cache: Dict[str, Tuple[List[str], List[str]]] = {}

def _get_cached_candidates(normalized_df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Cache drug and reaction candidates for faster matching. Uses DataFrame ID as cache key."""
    cache_key = f"{id(normalized_df)}"
    
    if cache_key not in _candidates_cache:
        # Only process unique values, limit to top 1000 to avoid performance issues
        drug_candidates = _unique_strings(normalized_df["drug_name"])[:1000] if "drug_name" in normalized_df else []
        react_candidates = _unique_strings(normalized_df["reaction"])[:1000] if "reaction" in normalized_df else []
        _candidates_cache[cache_key] = (drug_candidates, react_candidates)
    
    return _candidates_cache[cache_key]


def suggest_query_corrections(
    query: str,
    normalized_df: pd.DataFrame,
    threshold: float = 0.78,
    max_suggestions: int = 3,
) -> Dict[str, Tuple[str, float]]:
    """
    Suggest fuzzy corrections for tokens that look like drugs/reactions.

    Returns mapping of original term -> (suggested_term, score)
    """
    if normalized_df is None or normalized_df.empty:
        return {}

    tokens = [t.strip() for t in query.lower().replace("?", " ").split() if t.strip()]
    if not tokens:
        return {}

    # Use cached candidates for performance
    drug_candidates, react_candidates = _get_cached_candidates(normalized_df)
    all_candidates = list({*drug_candidates, *react_candidates})
    suggestions: Dict[str, Tuple[str, float]] = {}

    for token in tokens:
        if len(token) < 3:
            continue
        match = process.extractOne(token, all_candidates, scorer=fuzz.ratio)
        if match and match[1] / 100 >= threshold:
            suggestions[token] = (match[0], match[1] / 100)
            if len(suggestions) >= max_suggestions:
                break
    return suggestions


def get_corrected_query(query: str, corrections: Dict[str, Tuple[str, float]]) -> str:
    """
    Apply suggested corrections to the query.
    Handles case-insensitive replacement to preserve original query formatting.
    """
    import re
    corrected = query
    for original, (fixed, _) in corrections.items():
        # Case-insensitive replacement to handle mixed-case queries
        # Use word boundaries to avoid partial matches
        pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
        corrected = pattern.sub(fixed, corrected)
    return corrected


@st.cache_data
def find_top_candidates(
    normalized_df: pd.DataFrame,
    field: str,
    top_n: int = 10,
) -> List[str]:
    """
    Return top-N frequent values for a given field (drug_name or reaction).
    Cached for performance.
    """
    if normalized_df is None or normalized_df.empty or field not in normalized_df:
        return []
    series = (
        normalized_df[field]
        .dropna()
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
        .str.lower()
    )
    counts = series.value_counts()
    return counts.head(top_n).index.tolist()
