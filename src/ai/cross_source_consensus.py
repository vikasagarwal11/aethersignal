"""
Cross-Source Consensus Engine (Phase 2D.3)
Computes agreement scores across multiple data sources.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CrossSourceConsensusEngine:
    """
    Computes cross-source consensus for drug-reaction pairs.
    """
    
    # Source reliability weights (based on data quality)
    SOURCE_WEIGHTS = {
        "openfda": 1.0,  # Highest reliability
        "faers": 1.0,
        "dailymed": 0.9,  # Label information
        "clinicaltrials": 0.8,  # Controlled studies
        "pubmed": 0.7,  # Literature
        "ema": 0.9,  # Regulatory
        "yellowcard": 0.8,  # UK regulatory
        "health_canada": 0.8,  # Canadian regulatory
        "social": 0.5,  # Lower reliability (noise)
        "literature": 0.7
    }
    
    def __init__(self):
        """Initialize consensus engine."""
        pass
    
    def compute_consensus(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compute cross-source consensus for a drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction PT
            df: DataFrame with AE entries from multiple sources
        
        Returns:
            Dictionary with consensus metrics
        """
        # Filter for this drug-reaction pair
        filtered = df[
            (df["drug"].str.contains(drug, case=False, na=False)) &
            (df["reaction"] == reaction)
        ].copy()
        
        if filtered.empty:
            return {
                "consensus_score": 0.0,
                "source_count": 0,
                "sources": [],
                "weighted_consensus": 0.0
            }
        
        # Get unique sources
        if "source" not in filtered.columns:
            return {
                "consensus_score": 0.0,
                "source_count": 0,
                "sources": [],
                "weighted_consensus": 0.0
            }
        
        unique_sources = filtered["source"].unique().tolist()
        source_count = len(unique_sources)
        
        # Compute weighted consensus
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source in unique_sources:
            weight = self.SOURCE_WEIGHTS.get(source, 0.5)
            weighted_sum += weight
            total_weight += 1.0
        
        weighted_consensus = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Simple consensus (sources reporting / total available)
        # Assume 7-8 sources available
        available_sources = 8
        simple_consensus = min(source_count / available_sources, 1.0)
        
        # Combined consensus (weighted average)
        combined_consensus = (simple_consensus * 0.6) + (weighted_consensus * 0.4)
        
        # Get source breakdown
        source_breakdown = {}
        for source in unique_sources:
            source_df = filtered[filtered["source"] == source]
            source_breakdown[source] = {
                "count": len(source_df),
                "weight": self.SOURCE_WEIGHTS.get(source, 0.5),
                "avg_confidence": source_df["confidence"].mean() if "confidence" in source_df.columns else 0.0
            }
        
        return {
            "consensus_score": round(combined_consensus, 3),
            "simple_consensus": round(simple_consensus, 3),
            "weighted_consensus": round(weighted_consensus, 3),
            "source_count": source_count,
            "sources": unique_sources,
            "source_breakdown": source_breakdown
        }
    
    def get_source_agreement_matrix(
        self,
        df: pd.DataFrame,
        drug: str
    ) -> pd.DataFrame:
        """
        Get source agreement matrix for a drug.
        
        Args:
            df: DataFrame with AE entries
            drug: Drug name
        
        Returns:
            DataFrame with source × reaction agreement matrix
        """
        filtered = df[df["drug"].str.contains(drug, case=False, na=False)]
        
        if filtered.empty or "source" not in filtered.columns or "reaction" not in filtered.columns:
            return pd.DataFrame()
        
        # Create pivot table
        pivot = pd.crosstab(
            filtered["reaction"],
            filtered["source"],
            margins=False
        )
        
        return pivot

