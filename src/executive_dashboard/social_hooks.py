"""
Social → Executive Dashboard Hooks
Phase 2 Step 5: Integrates social intelligence into executive dashboard
"""

import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def social_to_executive_features(
    social_df: Optional[pd.DataFrame],
    faers_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Compute executive dashboard features from social AE data.
    
    Args:
        social_df: Social AE dataframe
        faers_df: Optional FAERS dataframe for comparison
    
    Returns:
        Dictionary of executive features
    """
    if social_df is None or social_df.empty:
        return {
            "total_social_posts": 0,
            "unique_drugs": 0,
            "unique_reactions": 0,
            "social_spikes": [],
            "social_novel_signals": [],
            "social_evidence_boost": 0.0
        }
    
    try:
        from src.social_ae.intelligence import SocialIntelligenceEngine
        intel_engine = SocialIntelligenceEngine()
    except Exception as e:
        logger.warning(f"Social intelligence engine not available: {e}")
        # Return basic metrics without intelligence features
        return {
            "total_social_posts": len(social_df),
            "unique_drugs": social_df.get("drug_match", pd.Series()).nunique() if "drug_match" in social_df.columns else 0,
            "unique_reactions": social_df.get("reaction", pd.Series()).nunique() if "reaction" in social_df.columns else 0,
            "social_spikes": [],
            "social_novel_signals": [],
            "social_evidence_boost": 0.0
        }
    
    # Basic metrics
    total_posts = len(social_df)
    unique_drugs = social_df.get("drug_match", pd.Series()).nunique() if "drug_match" in social_df.columns else 0
    unique_reactions = social_df.get("reaction", pd.Series()).nunique() if "reaction" in social_df.columns else 0
    
    # Intelligence features
    spikes = []
    novelty = []
    
    try:
        spikes = intel_engine.detect_spikes(social_df)
    except Exception as e:
        logger.warning(f"Spike detection failed: {e}")
    
    try:
        if faers_df is not None and not faers_df.empty:
            novelty = intel_engine.detect_novel_reactions(social_df, faers_df)
        else:
            # If no FAERS data, mark all social reactions as potentially novel
            if "reaction" in social_df.columns:
                reactions = social_df["reaction"].dropna().unique()
                novelty = [{"reaction": r, "social_count": 0, "faers_count": 0, "novel": True} for r in reactions[:10]]
    except Exception as e:
        logger.warning(f"Novelty detection failed: {e}")
    
    # Calculate evidence boost score
    # Higher score = more spikes + more novel signals
    evidence_boost = len(spikes) * 0.5 + len(novelty) * 1.0
    
    return {
        "total_social_posts": int(total_posts),
        "unique_drugs": int(unique_drugs),
        "unique_reactions": int(unique_reactions),
        "social_spikes": spikes,
        "social_novel_signals": novelty,
        "social_evidence_boost": float(evidence_boost)
    }


def merge_social_faers_executive(
    social_df: Optional[pd.DataFrame],
    faers_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Merge social and FAERS data for executive dashboard views.
    
    Args:
        social_df: Social AE dataframe
        faers_df: FAERS dataframe
    
    Returns:
        Combined dataframe with source labels
    """
    combined_data = []
    
    # Add social data
    if social_df is not None and not social_df.empty:
        social_subset = social_df.copy()
        social_subset["source"] = "Social"
        if "reaction" in social_subset.columns:
            reaction_counts = social_subset.groupby("reaction").size()
            for reaction, count in reaction_counts.items():
                combined_data.append({
                    "reaction": reaction,
                    "total_mentions": int(count),
                    "source": "Social"
                })
    
    # Add FAERS data
    if faers_df is not None and not faers_df.empty:
        faers_subset = faers_df.copy()
        faers_subset["source"] = "FAERS"
        if "reaction" in faers_subset.columns:
            reaction_counts = faers_subset.groupby("reaction").size()
            for reaction, count in reaction_counts.items():
                combined_data.append({
                    "reaction": reaction,
                    "total_mentions": int(count),
                    "source": "FAERS"
                })
    
    if not combined_data:
        return pd.DataFrame(columns=["reaction", "total_mentions", "source"])
    
    # Combine and aggregate
    combined_df = pd.DataFrame(combined_data)
    
    # Aggregate by reaction (sum across sources)
    if not combined_df.empty:
        reaction_totals = combined_df.groupby("reaction")["total_mentions"].sum().reset_index()
        reaction_totals = reaction_totals.sort_values("total_mentions", ascending=False)
        return reaction_totals
    
    return pd.DataFrame(columns=["reaction", "total_mentions"])

