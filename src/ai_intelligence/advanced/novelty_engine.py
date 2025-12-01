"""
Novel Signal Detection Engine
Detects reactions that appear in one source but not others, or show unusual patterns
"""

import logging
from typing import List, Dict, Set, Any
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NoveltyEngine:
    """Detects novel adverse events across multiple sources."""
    
    def detect(
        self,
        label_set: List[str],
        faers_set: List[str],
        social_set: List[str],
        literature_set: List[str]
    ) -> Dict[str, Any]:
        """
        Detect novel reactions across sources.
        
        Args:
            label_set: Reactions listed in FDA label
            faers_set: Reactions reported in FAERS
            social_set: Reactions mentioned in social media
            literature_set: Reactions found in literature
        
        Returns:
            Dictionary with novel reaction categories
        """
        # Convert to sets for efficient operations
        label_set = set(label_set) if label_set else set()
        faers_set = set(faers_set) if faers_set else set()
        social_set = set(social_set) if social_set else set()
        literature_set = set(literature_set) if literature_set else set()
        
        # All detected reactions
        all_detected = faers_set | social_set | literature_set
        
        # Novel reactions (not in label)
        novel = all_detected - label_set
        
        # Source-specific novel reactions
        in_social_only = social_set - label_set - faers_set - literature_set
        in_literature_only = literature_set - label_set - faers_set - social_set
        in_faers_only = faers_set - label_set - social_set - literature_set
        
        # Cross-source novel (in multiple sources but not label)
        cross_source_novel = (faers_set | social_set | literature_set) - label_set
        cross_source_novel = {
            r for r in cross_source_novel
            if sum([r in faers_set, r in social_set, r in literature_set]) >= 2
        }
        
        return {
            "novel_reactions": list(novel),
            "in_social_only": list(in_social_only),
            "in_literature_only": list(in_literature_only),
            "in_faers_only": list(in_faers_only),
            "cross_source_novel": list(cross_source_novel),
            "total_novel_count": len(novel),
            "label_coverage": len(label_set),
            "detected_coverage": len(all_detected)
        }
    
    def detect_spikes(
        self,
        df: pd.DataFrame,
        reaction_col: str = "reaction",
        date_col: str = "timestamp",
        threshold_multiplier: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect reactions that spike significantly over time.
        
        Args:
            df: DataFrame with reaction and timestamp columns
            reaction_col: Name of reaction column
            date_col: Name of date/timestamp column
            threshold_multiplier: Multiplier for spike detection (e.g., 2.0 = 2x average)
        
        Returns:
            List of spike detections
        """
        if df.empty or reaction_col not in df.columns or date_col not in df.columns:
            return []
        
        try:
            # Convert date column
            df[date_col] = pd.to_datetime(df[date_col])
            df["date"] = df[date_col].dt.date
            
            # Group by reaction and date
            daily_counts = df.groupby([reaction_col, "date"]).size().reset_index(name="count")
            
            # Calculate rolling averages
            spikes = []
            for reaction in daily_counts[reaction_col].unique():
                reaction_data = daily_counts[daily_counts[reaction_col] == reaction].copy()
                reaction_data = reaction_data.sort_values("date")
                
                # Calculate 7-day rolling average
                reaction_data["rolling_avg"] = reaction_data["count"].rolling(window=7, min_periods=1).mean()
                
                # Detect spikes
                reaction_data["is_spike"] = reaction_data["count"] > (reaction_data["rolling_avg"] * threshold_multiplier)
                
                spike_days = reaction_data[reaction_data["is_spike"]]
                if not spike_days.empty:
                    for _, row in spike_days.iterrows():
                        spikes.append({
                            "reaction": reaction,
                            "date": row["date"],
                            "count": row["count"],
                            "average": row["rolling_avg"],
                            "spike_ratio": row["count"] / row["rolling_avg"] if row["rolling_avg"] > 0 else 0
                        })
            
            return sorted(spikes, key=lambda x: x["spike_ratio"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting spikes: {e}")
            return []

