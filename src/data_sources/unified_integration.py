"""
Unified Integration Layer - Routes all data sources through Reaction Intelligence Core.
This ensures all sources get normalized, embedded, clustered, and harmonized.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

from .data_source_manager_v2 import DataSourceManagerV2
from src.social_ae.reaction_intelligence import ReactionIntelligenceCore
from src.social_ae.reaction_embeddings import ReactionEmbeddingEngine
from src.normalization.reaction_normalizer import ReactionNormalizer

logger = logging.getLogger(__name__)


class UnifiedSourceIntegration:
    """
    Master integration layer that routes all data sources through Reaction Intelligence Core.
    
    Features:
    - Normalizes all reactions to PTs
    - Generates embeddings for all reactions
    - Adds to vector store
    - Provides unified output format
    - Handles cross-source deduplication
    """
    
    def __init__(
        self,
        ds_manager: Optional[DataSourceManagerV2] = None,
        supabase_client=None
    ):
        """
        Initialize unified integration.
        
        Args:
            ds_manager: Optional DataSourceManagerV2 instance
            supabase_client: Optional Supabase client for vector store
        """
        self.ds_manager = ds_manager or DataSourceManagerV2()
        self.embedding_engine = ReactionEmbeddingEngine()
        self.normalizer = ReactionNormalizer(
            embedding_engine=self.embedding_engine,
            use_llm=False
        )
        self.intelligence_core = ReactionIntelligenceCore(
            embedding_engine=self.embedding_engine,
            normalizer=self.normalizer,
            supabase_client=supabase_client
        )
    
    def fetch_and_normalize(
        self,
        drug: str,
        days_back: int = 30,
        sources: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch from all enabled sources and normalize through Reaction Intelligence Core.
        
        Args:
            drug: Drug name
            days_back: Days to look back
            sources: Optional list of source names to fetch from
        
        Returns:
            DataFrame with normalized, embedded, categorized reactions
        """
        # Fetch from all sources
        all_results = []
        
        if sources:
            # Fetch from specific sources
            for source_name in sources:
                try:
                    results = self.ds_manager.fetch_by_source(source_name, {"drug": drug})
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Error fetching from {source_name}: {str(e)}")
        else:
            # Fetch from all enabled sources
            all_results = self.ds_manager.fetch_all({"drug": drug})
        
        if not all_results:
            return pd.DataFrame()
        
        # Normalize all reactions through Reaction Intelligence Core
        normalized_rows = []
        
        for entry in all_results:
            reactions = entry.get("reactions", [])
            if not reactions:
                # Single reaction
                reaction = entry.get("reaction")
                if reaction:
                    reactions = [reaction]
            
            if not reactions:
                continue
            
            # Normalize each reaction
            for reaction_raw in reactions:
                normalized = self.normalizer.normalize(reaction_raw, drug)
                
                # Generate embedding
                embedding = self.embedding_engine.embed(reaction_raw)
                
                # Add to vector store
                if embedding is not None:
                    self.intelligence_core.similarity_engine.add_to_store(
                        reaction_raw=reaction_raw,
                        reaction_norm=normalized["pt"],
                        embedding=embedding,
                        drug=drug,
                        source=entry.get("source", "unknown")
                    )
                
                # Create normalized row
                row = {
                    "timestamp": entry.get("timestamp"),
                    "drug": drug,
                    "reaction_raw": reaction_raw,
                    "reaction": normalized["pt"],
                    "reaction_category": normalized["category"],
                    "normalization_method": normalized["method"],
                    "normalization_confidence": normalized["confidence"],
                    "confidence": entry.get("confidence", 0.0),
                    "severity": entry.get("severity", 0.0),
                    "text": entry.get("text", "")[:500],
                    "source": entry.get("source", "unknown"),
                    "metadata": entry.get("metadata", {}),
                    "has_embedding": embedding is not None
                }
                
                normalized_rows.append(row)
        
        df = pd.DataFrame(normalized_rows)
        
        return df
    
    def get_source_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about sources in the dataset.
        
        Args:
            df: DataFrame with normalized reactions
        
        Returns:
            Dictionary with source statistics
        """
        if df.empty:
            return {}
        
        stats = {
            "total_entries": len(df),
            "unique_reactions": df["reaction"].nunique(),
            "sources": {}
        }
        
        for source in df["source"].unique():
            source_df = df[df["source"] == source]
            stats["sources"][source] = {
                "count": len(source_df),
                "unique_reactions": source_df["reaction"].nunique(),
                "avg_confidence": source_df["confidence"].mean(),
                "avg_severity": source_df["severity"].mean()
            }
        
        return stats
    
    def get_cross_source_agreement(
        self,
        df: pd.DataFrame,
        drug: str,
        reaction: str
    ) -> Dict[str, Any]:
        """
        Calculate cross-source agreement for a drug-reaction pair.
        
        Args:
            df: DataFrame with normalized reactions
            drug: Drug name
            reaction: Reaction PT
        
        Returns:
            Dictionary with agreement metrics
        """
        filtered = df[(df["drug"].str.contains(drug, case=False, na=False)) &
                      (df["reaction"] == reaction)]
        
        if filtered.empty:
            return {"agreement": 0.0, "sources": []}
        
        sources = filtered["source"].unique().tolist()
        source_count = len(sources)
        
        # Agreement score: more sources = higher agreement
        agreement = min(source_count / 5.0, 1.0)  # Normalize to 0-1
        
        return {
            "agreement": agreement,
            "sources": sources,
            "count": len(filtered),
            "avg_confidence": filtered["confidence"].mean(),
            "avg_severity": filtered["severity"].mean()
        }

