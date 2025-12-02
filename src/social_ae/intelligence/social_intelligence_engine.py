"""
Social Intelligence Engine - Advanced analysis for social AE data
Phase 2: Intelligence features for Social AE module
"""

import numpy as np
import pandas as pd
from datetime import timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SocialIntelligenceEngine:
    """
    Central engine for all Social AE intelligence tasks:
    - Spike detection
    - Novelty detection (Social > FAERS)
    - Clustering
    - Cross-linking with FAERS
    - Explainability
    """
    
    def __init__(self):
        self.min_cluster_size = 5
        self.min_spike_ratio = 2.0
    
    # ------------------------------------------------------
    # 1) Spike Detection
    # ------------------------------------------------------
    def detect_spikes(
        self, 
        df: pd.DataFrame, 
        date_col: str = "created_date",
        drug_col: Optional[str] = None,
        reaction_col: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect spikes in social AE activity.
        
        Args:
            df: Social AE dataframe
            date_col: Name of date column
            drug_col: Optional drug column for drug-specific spikes
            reaction_col: Optional reaction column for reaction-specific spikes
        
        Returns:
            List of spike events with date and count
        """
        if df.empty:
            return []
        
        try:
            # Convert date column
            if date_col not in df.columns:
                # Try common date column names
                for col in ["created_utc", "date", "timestamp", "created_at"]:
                    if col in df.columns:
                        date_col = col
                        break
                else:
                    logger.warning("No date column found for spike detection")
                    return []
            
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            
            if df.empty:
                return []
            
            # Group by date
            ts = df.groupby(df[date_col].dt.date).size()
            
            if len(ts) < 3:
                return []
            
            # Calculate moving average
            ma = ts.rolling(window=3, min_periods=1).mean()
            
            # Detect spikes (values > 2x moving average)
            spikes = ts[ts > (ma * self.min_spike_ratio)]
            
            result = []
            for date_idx, count in spikes.items():
                result.append({
                    "date": str(date_idx),
                    "count": int(count),
                    "baseline_avg": float(ma.get(date_idx, 0))
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting spikes: {e}")
            return []
    
    # ------------------------------------------------------
    # 2) Novelty Detection: Social > FAERS
    # ------------------------------------------------------
    def detect_novel_reactions(
        self, 
        social_df: pd.DataFrame, 
        faers_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect reactions present in social data but not in FAERS.
        
        Args:
            social_df: Social AE dataframe
            faers_df: Optional FAERS dataframe for comparison
        
        Returns:
            List of novel reactions with metadata
        """
        if social_df.empty:
            return []
        
        try:
            # Get social reactions
            if "reaction" not in social_df.columns:
                logger.warning("No 'reaction' column in social data")
                return []
            
            social_reactions = set(
                social_df["reaction"]
                .dropna()
                .str.lower()
                .str.strip()
                .unique()
            )
            
            # If no FAERS data provided, return all social reactions as potentially novel
            if faers_df is None or faers_df.empty:
                return [
                    {"reaction": r, "social_count": 0, "faers_count": 0, "novel": True}
                    for r in social_reactions
                ]
            
            # Get FAERS reactions
            if "reaction" not in faers_df.columns:
                faers_reactions = set()
            else:
                faers_reactions = set(
                    faers_df["reaction"]
                    .dropna()
                    .str.lower()
                    .str.strip()
                    .unique()
                )
            
            # Find novel reactions
            novel_reactions = social_reactions - faers_reactions
            
            # Build result with counts
            result = []
            for reaction in novel_reactions:
                social_count = len(social_df[social_df["reaction"].str.lower().str.strip() == reaction])
                result.append({
                    "reaction": reaction.title(),  # Capitalize for display
                    "social_count": int(social_count),
                    "faers_count": 0,
                    "novel": True
                })
            
            # Sort by social count (most frequent novel reactions first)
            result.sort(key=lambda x: x["social_count"], reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting novel reactions: {e}")
            return []
    
    # ------------------------------------------------------
    # 3) Lightweight Clustering
    # ------------------------------------------------------
    def cluster_posts(
        self, 
        df: pd.DataFrame, 
        text_col: str = "clean_text",
        n_clusters: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Cluster social posts by content similarity.
        
        Args:
            df: Social AE dataframe
            text_col: Name of text column to cluster on
            n_clusters: Number of clusters to create
        
        Returns:
            List of cluster summaries
        """
        if df.empty or len(df) < self.min_cluster_size:
            return []
        
        try:
            # Check if text column exists
            if text_col not in df.columns:
                # Try common text column names
                for col in ["text", "post_text", "content", "body"]:
                    if col in df.columns:
                        text_col = col
                        break
                else:
                    logger.warning("No text column found for clustering")
                    return []
            
            # Simple TF-IDF + KMeans clustering
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.cluster import KMeans
            except ImportError:
                logger.warning("scikit-learn not available, skipping clustering")
                return []
            
            # Prepare text data
            texts = df[text_col].fillna("").astype(str).tolist()
            
            if not texts:
                return []
            
            # Vectorize
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=200,
                min_df=2
            )
            X = vectorizer.fit_transform(texts)
            
            # Adjust n_clusters if needed
            actual_clusters = min(n_clusters, len(df))
            if actual_clusters < 2:
                return []
            
            # Cluster
            kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
            
            df["cluster"] = clusters
            
            # Build summaries
            summaries = []
            for c in range(actual_clusters):
                subset = df[df["cluster"] == c]
                if len(subset) == 0:
                    continue
                
                # Get example texts
                examples = subset[text_col].head(3).tolist()
                
                summaries.append({
                    "cluster_id": int(c),
                    "size": int(len(subset)),
                    "examples": examples,
                    "percentage": round(len(subset) / len(df) * 100, 1)
                })
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error clustering posts: {e}")
            return []
    
    # ------------------------------------------------------
    # 4) Cross-Link Social → FAERS
    # ------------------------------------------------------
    def crosslink_faers(
        self, 
        social_df: pd.DataFrame, 
        faers_df: Optional[pd.DataFrame],
        drug_col: str = "drug_match",
        reaction_col: str = "reaction"
    ) -> List[Dict[str, Any]]:
        """
        Cross-link social AE data with FAERS evidence.
        
        Args:
            social_df: Social AE dataframe
            faers_df: FAERS dataframe
            drug_col: Drug column name
            reaction_col: Reaction column name
        
        Returns:
            List of cross-linked evidence records
        """
        if social_df.empty:
            return []
        
        if faers_df is None or faers_df.empty:
            return []
        
        try:
            # Normalize column names
            social_drug = drug_col if drug_col in social_df.columns else None
            social_reaction = reaction_col if reaction_col in social_df.columns else None
            
            if not social_drug or not social_reaction:
                logger.warning("Missing required columns for cross-linking")
                return []
            
            # Normalize FAERS columns
            faers_drug = drug_col if drug_col in faers_df.columns else "drug"
            faers_reaction = reaction_col if reaction_col in faers_df.columns else "reaction"
            
            if faers_drug not in faers_df.columns or faers_reaction not in faers_df.columns:
                logger.warning("FAERS data missing required columns")
                return []
            
            # Merge on drug and reaction (case-insensitive)
            social_normalized = social_df.copy()
            social_normalized["drug_lower"] = social_normalized[social_drug].str.lower().str.strip()
            social_normalized["reaction_lower"] = social_normalized[social_reaction].str.lower().str.strip()
            
            faers_normalized = faers_df.copy()
            faers_normalized["drug_lower"] = faers_normalized[faers_drug].str.lower().str.strip()
            faers_normalized["reaction_lower"] = faers_normalized[faers_reaction].str.lower().str.strip()
            
            # Merge
            merged = pd.merge(
                social_normalized,
                faers_normalized,
                on=["drug_lower", "reaction_lower"],
                how="inner",
                suffixes=("_social", "_faers")
            )
            
            if merged.empty:
                return []
            
            # Build evidence records
            evidence = []
            for _, row in merged.head(20).iterrows():  # Limit to 20 for performance
                evidence.append({
                    "drug": str(row.get(social_drug, "")),
                    "reaction": str(row.get(social_reaction, "")),
                    "social_date": str(row.get("created_date", "")) if "created_date" in row else "",
                    "faers_date": str(row.get("event_date", "")) if "event_date" in row else "",
                    "match_type": "exact"
                })
            
            return evidence
            
        except Exception as e:
            logger.error(f"Error cross-linking with FAERS: {e}")
            return []
    
    # ------------------------------------------------------
    # 5) Explainability (Mini LLM)
    # ------------------------------------------------------
    def explain_social_pattern(
        self, 
        drug: str, 
        reaction: str, 
        spike_info: Optional[Dict] = None,
        novel_flag: bool = False
    ) -> str:
        """
        Generate human-readable explanation of social pattern.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            spike_info: Optional spike information
            novel_flag: Whether this is a novel reaction
        
        Returns:
            Explanation text
        """
        reasons = []
        
        if spike_info:
            date = spike_info.get("date", "recently")
            count = spike_info.get("count", 0)
            reasons.append(
                f"There is a recent spike in social media mentions of {drug} "
                f"associated with {reaction} on {date} ({count} posts)."
            )
        
        if novel_flag:
            reasons.append(
                f"The reaction {reaction} appears in social media data but has not "
                f"yet been reported in FAERS, suggesting this may be an emerging signal."
            )
        
        if not reasons:
            return f"Social media data shows mentions of {drug} and {reaction}, but no unusual patterns detected."
        
        return " ".join(reasons)

