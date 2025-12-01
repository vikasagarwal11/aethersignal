"""
Emerging Reaction Discovery Engine
Discovers new reactions not in dictionary that appear frequently.
"""

import pandas as pd
from typing import List, Dict, Optional
from collections import Counter
import logging

from src.normalization.reaction_normalizer import ReactionNormalizer
from src.normalization.reaction_dictionary import get_reaction_pt

logger = logging.getLogger(__name__)


class ReactionDiscoveryEngine:
    """
    Discovers emerging reactions that aren't in the dictionary.
    """
    
    def __init__(self, normalizer: Optional[ReactionNormalizer] = None):
        """
        Initialize discovery engine.
        
        Args:
            normalizer: Optional reaction normalizer
        """
        self.normalizer = normalizer
    
    def discover_emerging_reactions(
        self,
        df: pd.DataFrame,
        reaction_col: str = "reaction",
        min_count: int = 5,
        drug: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Discover reactions that appear frequently but aren't in dictionary.
        
        Args:
            df: DataFrame with reactions
            reaction_col: Column name containing reactions
            min_count: Minimum occurrence count
            drug: Optional drug name for filtering
        
        Returns:
            DataFrame with emerging reactions
        """
        if df.empty or reaction_col not in df.columns:
            return pd.DataFrame()
        
        # Filter by drug if provided
        if drug and "drug" in df.columns:
            df = df[df["drug"].str.contains(drug, case=False, na=False)]
        
        # Get raw reactions
        reactions = df[reaction_col].dropna().astype(str).str.lower().str.strip()
        
        # Count occurrences
        reaction_counts = Counter(reactions)
        
        # Find reactions not in dictionary
        emerging = []
        for reaction, count in reaction_counts.items():
            if count >= min_count:
                # Check if it's already normalized
                pt = get_reaction_pt(reaction)
                
                # If no PT found or PT is same as original (not normalized), it's emerging
                if not pt or pt.lower() == reaction:
                    # Try normalization
                    if self.normalizer:
                        normalized = self.normalizer.normalize(reaction, drug)
                        if normalized["method"] == "none" or normalized["confidence"] < 0.5:
                            emerging.append({
                                "reaction_raw": reaction,
                                "count": count,
                                "normalized_pt": normalized["pt"],
                                "normalization_method": normalized["method"],
                                "confidence": normalized["confidence"]
                            })
                    else:
                        emerging.append({
                            "reaction_raw": reaction,
                            "count": count,
                            "normalized_pt": reaction.title(),
                            "normalization_method": "none",
                            "confidence": 0.0
                        })
        
        if not emerging:
            return pd.DataFrame()
        
        emerging_df = pd.DataFrame(emerging)
        emerging_df = emerging_df.sort_values("count", ascending=False)
        
        return emerging_df
    
    def suggest_pt_for_reaction(
        self,
        reaction: str,
        similar_reactions: Optional[List[str]] = None,
        drug: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Suggest Preferred Term for an emerging reaction.
        
        Args:
            reaction: Reaction term
            similar_reactions: Optional list of similar reactions
            drug: Optional drug name
        
        Returns:
            Dictionary with PT suggestion and confidence
        """
        if self.normalizer:
            normalized = self.normalizer.normalize(reaction, drug)
            return {
                "suggested_pt": normalized["pt"],
                "confidence": normalized["confidence"],
                "method": normalized["method"],
                "category": normalized["category"],
                "similar_reactions": similar_reactions or []
            }
        
        return {
            "suggested_pt": reaction.title(),
            "confidence": 0.0,
            "method": "none",
            "category": "Other",
            "similar_reactions": similar_reactions or []
        }

