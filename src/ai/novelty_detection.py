"""
Novelty Detection Engine (Phase 2D.4)
Detects novel adverse events not previously seen in labels, FAERS, or other sources.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NoveltyDetectionEngine:
    """
    Detects novel adverse events.
    """
    
    def __init__(self):
        """Initialize novelty detection engine."""
        pass
    
    def compute_novelty_score(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame,
        label_reactions: Optional[List[str]] = None,
        historical_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Compute novelty score for a drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction PT
            df: Current DataFrame with AE entries
            label_reactions: Optional list of known label reactions
            historical_df: Optional historical DataFrame for comparison
        
        Returns:
            Dictionary with novelty metrics
        """
        novelty_factors = {}
        
        # 1. Check if in label
        is_labeled = False
        if label_reactions:
            is_labeled = any(
                reaction.lower() in known.lower() or known.lower() in reaction.lower()
                for known in label_reactions
            )
        novelty_factors["in_label"] = is_labeled
        
        # 2. Check if in FAERS historically
        in_faers_historical = False
        if historical_df is not None:
            faers_historical = historical_df[
                (historical_df["drug"].str.contains(drug, case=False, na=False)) &
                (historical_df["reaction"] == reaction) &
                (historical_df["source"].isin(["faers", "openfda"]))
            ]
            in_faers_historical = len(faers_historical) > 0
        novelty_factors["in_faers_historical"] = in_faers_historical
        
        # 3. Check if in DailyMed
        in_dailymed = False
        if "source" in df.columns:
            dailymed_entries = df[
                (df["source"] == "dailymed") &
                (df["reaction"] == reaction)
            ]
            in_dailymed = len(dailymed_entries) > 0
        novelty_factors["in_dailymed"] = in_dailymed
        
        # 4. Check if in EMA/UK/Canada
        in_regulatory = False
        if "source" in df.columns:
            regulatory_sources = ["ema", "yellowcard", "health_canada"]
            regulatory_entries = df[
                (df["source"].isin(regulatory_sources)) &
                (df["reaction"] == reaction)
            ]
            in_regulatory = len(regulatory_entries) > 0
        novelty_factors["in_regulatory"] = in_regulatory
        
        # 5. Check if in PubMed historically
        in_pubmed = False
        if "source" in df.columns:
            pubmed_entries = df[
                (df["source"].isin(["pubmed", "literature"])) &
                (df["reaction"] == reaction)
            ]
            in_pubmed = len(pubmed_entries) > 0
        novelty_factors["in_pubmed"] = in_pubmed
        
        # 6. Check if only in social media (most novel)
        only_social = False
        if "source" in df.columns:
            social_entries = df[df["source"].isin(["social", "reddit", "x", "twitter"])]
            other_entries = df[~df["source"].isin(["social", "reddit", "x", "twitter"])]
            only_social = len(social_entries) > 0 and len(other_entries) == 0
        novelty_factors["only_social"] = only_social
        
        # 7. Check recency (first appearance)
        first_appearance_days = None
        if "timestamp" in df.columns:
            try:
                df["date"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df[df["date"].notna()]
                if not df.empty:
                    first_date = df["date"].min()
                    days_ago = (datetime.now() - first_date).days
                    first_appearance_days = days_ago
            except Exception:
                pass
        novelty_factors["first_appearance_days"] = first_appearance_days
        
        # Compute novelty score
        novelty_score = 0.0
        
        # Known labeled AE = 0.0
        if is_labeled:
            novelty_score = 0.0
        # Post-marketing new signal = 0.6
        elif in_faers_historical or in_dailymed or in_regulatory:
            novelty_score = 0.6
        # Social-only emerging pattern = 0.8
        elif only_social:
            novelty_score = 0.8
        # New across multiple sources = 1.0
        elif not in_faers_historical and not in_dailymed and not in_regulatory:
            if first_appearance_days and first_appearance_days <= 90:
                novelty_score = 1.0
            else:
                novelty_score = 0.7
        
        return {
            "novelty_score": round(novelty_score, 3),
            "factors": novelty_factors,
            "is_novel": novelty_score >= 0.6,
            "novelty_level": self._categorize_novelty(novelty_score)
        }
    
    def _categorize_novelty(self, score: float) -> str:
        """Categorize novelty level."""
        if score >= 0.9:
            return "highly_novel"
        elif score >= 0.7:
            return "novel"
        elif score >= 0.4:
            return "moderately_novel"
        else:
            return "known"

