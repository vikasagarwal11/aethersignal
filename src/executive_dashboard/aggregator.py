"""
Executive Aggregator - Phase 3J
Computes metrics, trends, rankings, and insights for executive dashboard.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .config import is_feature_enabled

logger = logging.getLogger(__name__)


class ExecutiveAggregator:
    """
    Aggregates and computes executive-level metrics from unified AE data.
    """
    
    def __init__(self):
        """Initialize aggregator."""
        pass
    
    def compute_kpis(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Compute Key Performance Indicators.
        
        Args:
            df: Unified AE DataFrame
            drug: Optional drug filter
            days_back: Days to compare
        
        Returns:
            Dictionary with KPI metrics
        """
        if df.empty:
            return self._empty_kpis()
        
        # Filter by drug if specified
        if drug:
            df = df[df["drug"].str.contains(drug, case=False, na=False)]
        
        if df.empty:
            return self._empty_kpis()
        
        # Total AE count
        total_ae = len(df)
        
        # Recent counts
        cutoff_date = datetime.now() - timedelta(days=days_back)
        if "created_date" in df.columns:
            df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
            recent_df = df[df["created_date"] >= cutoff_date]
            recent_count = len(recent_df)
        else:
            recent_count = total_ae
        
        # Previous period for comparison
        prev_cutoff = cutoff_date - timedelta(days=days_back)
        if "created_date" in df.columns:
            prev_df = df[
                (df["created_date"] >= prev_cutoff) & 
                (df["created_date"] < cutoff_date)
            ]
            prev_count = len(prev_df)
        else:
            prev_count = 0
        
        # Calculate change percentage
        if prev_count > 0:
            change_pct = ((recent_count - prev_count) / prev_count) * 100
        else:
            change_pct = 0.0 if recent_count == 0 else 100.0
        
        # Top reaction
        top_reaction = df["reaction"].value_counts().idxmax() if total_ae > 0 else None
        top_reaction_count = df["reaction"].value_counts().max() if total_ae > 0 else 0
        
        # Most severe emerging reaction
        if "severity_score" in df.columns and not df.empty:
            severe_df = df[df["severity_score"] >= 0.7]
            if not severe_df.empty:
                severe_reaction = severe_df["reaction"].value_counts().idxmax()
                severe_count = severe_df["reaction"].value_counts().max()
            else:
                severe_reaction = None
                severe_count = 0
        else:
            severe_reaction = None
            severe_count = 0
        
        # Novel signal count (reactions not in common dictionary)
        if "reaction_pt" in df.columns:
            novel_df = df[df["reaction_pt"] == df["reaction"]]
            novel_count = novel_df["reaction"].nunique()
        else:
            novel_count = 0
        
        # Average quantum score
        if "quantum_score" in df.columns:
            avg_quantum = df["quantum_score"].mean()
        else:
            avg_quantum = 0.0
        
        return {
            "total_ae": total_ae,
            "recent_count": recent_count,
            "change_pct": round(change_pct, 1),
            "top_reaction": top_reaction,
            "top_reaction_count": top_reaction_count,
            "severe_reaction": severe_reaction,
            "severe_count": severe_count,
            "novel_signal_count": novel_count,
            "avg_quantum_score": round(avg_quantum, 3)
        }
    
    def compute_trends(
        self,
        df: pd.DataFrame,
        period: str = "M"  # M=monthly, W=weekly, D=daily
    ) -> pd.DataFrame:
        """
        Compute time-series trends.
        
        Args:
            df: Unified AE DataFrame
            period: Aggregation period (M, W, D)
        
        Returns:
            DataFrame with trend data
        """
        if df.empty or "created_date" not in df.columns:
            return pd.DataFrame({"period": [], "count": []})
        
        df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
        df = df[df["created_date"].notna()]
        
        if df.empty:
            return pd.DataFrame({"period": [], "count": []})
        
        # Group by period
        df["period"] = df["created_date"].dt.to_period(period)
        trend = df.groupby("period").size().reset_index(name="count")
        trend["period_str"] = trend["period"].astype(str)
        
        return trend[["period_str", "count"]]
    
    def compute_source_trends(
        self,
        df: pd.DataFrame,
        period: str = "M"
    ) -> pd.DataFrame:
        """
        Compute trends by source.
        
        Args:
            df: Unified AE DataFrame
            period: Aggregation period
        
        Returns:
            DataFrame with trends by source
        """
        if df.empty or "created_date" not in df.columns or "source" not in df.columns:
            return pd.DataFrame()
        
        df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
        df = df[df["created_date"].notna()]
        
        if df.empty:
            return pd.DataFrame()
        
        df["period"] = df["created_date"].dt.to_period(period)
        trend = df.groupby(["period", "source"]).size().reset_index(name="count")
        trend["period_str"] = trend["period"].astype(str)
        
        return trend
    
    def compute_signal_ranking(
        self,
        df: pd.DataFrame,
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Compute ranked signal list.
        
        Args:
            df: Unified AE DataFrame
            limit: Maximum number of signals to return
        
        Returns:
            DataFrame with ranked signals
        """
        if df.empty:
            return pd.DataFrame()
        
        # Group by drug-reaction pair
        grouped = df.groupby(["drug", "reaction"]).agg({
            "quantum_score": "mean",
            "severity_score": "mean",
            "confidence": "mean",
            "created_date": "count"
        }).reset_index()
        
        grouped.columns = ["drug", "reaction", "quantum_score", "severity_score", "confidence", "frequency"]
        
        # Calculate acceleration (recent vs older)
        cutoff_date = datetime.now() - timedelta(days=30)
        if "created_date" in df.columns:
            df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
            recent_df = df[df["created_date"] >= cutoff_date]
            recent_grouped = recent_df.groupby(["drug", "reaction"]).size().reset_index(name="recent_count")
            
            grouped = grouped.merge(recent_grouped, on=["drug", "reaction"], how="left")
            grouped["recent_count"] = grouped["recent_count"].fillna(0)
            grouped["acceleration"] = (grouped["recent_count"] / grouped["frequency"]).fillna(0)
        else:
            grouped["acceleration"] = 0.0
        
        # Calculate novelty (placeholder - would use novelty engine)
        grouped["novelty"] = 0.5  # Placeholder
        
        # Sort by quantum score
        grouped = grouped.sort_values("quantum_score", ascending=False)
        
        return grouped.head(limit)
    
    def compute_novelty_signals(
        self,
        df: pd.DataFrame,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        Compute novel signals (reactions appearing in new sources).
        
        Args:
            df: Unified AE DataFrame
            limit: Maximum number of signals to return
        
        Returns:
            DataFrame with novel signals
        """
        if df.empty:
            return pd.DataFrame()
        
        # Reactions that appear in social/literature but not FAERS
        if "source" in df.columns:
            faers_reactions = set(df[df["source"].str.contains("faers", case=False, na=False)]["reaction"].unique())
            social_reactions = set(df[df["source"].str.contains("social", case=False, na=False)]["reaction"].unique())
            lit_reactions = set(df[df["source"].str.contains("literature", case=False, na=False)]["reaction"].unique())
            
            # Novel: in social/lit but not FAERS
            novel_reactions = (social_reactions | lit_reactions) - faers_reactions
            
            novel_df = df[df["reaction"].isin(novel_reactions)]
            
            if not novel_df.empty:
                grouped = novel_df.groupby(["drug", "reaction"]).agg({
                    "quantum_score": "mean",
                    "severity_score": "mean",
                    "created_date": "count"
                }).reset_index()
                grouped.columns = ["drug", "reaction", "quantum_score", "severity_score", "count"]
                grouped = grouped.sort_values("quantum_score", ascending=False)
                return grouped.head(limit)
        
        return pd.DataFrame()
    
    def _empty_kpis(self) -> Dict[str, Any]:
        """Return empty KPIs structure."""
        return {
            "total_ae": 0,
            "recent_count": 0,
            "change_pct": 0.0,
            "top_reaction": None,
            "top_reaction_count": 0,
            "severe_reaction": None,
            "severe_count": 0,
            "novel_signal_count": 0,
            "avg_quantum_score": 0.0
        }

