"""
Global Indexing & Performance Layer (Phase 3A.6)
Manages indexes, caches, and performance optimizations.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class GlobalIndexer:
    """
    Global indexing and performance layer.
    Manages indexes, caches, and refresh schedules.
    """
    
    def __init__(self, storage):
        """
        Initialize global indexer.
        
        Args:
            storage: UnifiedStorageEngine instance
        """
        self.storage = storage
        self.caches = {
            "trend_cache": {},
            "recent_ae_cache": {},
            "reaction_cluster_cache": {},
            "drug_synonym_cache": {},
            "llm_explanation_cache": {}
        }
    
    def refresh_trend_cache(self, drug: str, days: int = 30):
        """
        Refresh trend cache for a drug.
        
        Args:
            drug: Drug name
            days: Days to look back
        """
        cache_key = f"{drug}_{days}"
        
        try:
            from src.storage.federated_query_engine import FederatedQueryEngine
            query_engine = FederatedQueryEngine(self.storage)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = query_engine.query(
                drug=drug,
                date_range=(start_date, end_date),
                limit=10000
            )
            
            if not df.empty and "event_date" in df.columns:
                # Group by date
                df["date"] = pd.to_datetime(df["event_date"]).dt.date
                trend = df.groupby("date").size().reset_index(name="count")
                
                self.caches["trend_cache"][cache_key] = {
                    "data": trend.to_dict("records"),
                    "cached_at": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error refreshing trend cache: {str(e)}")
    
    def get_trend_cache(self, drug: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get cached trend data."""
        cache_key = f"{drug}_{days}"
        cached = self.caches["trend_cache"].get(cache_key)
        
        if cached:
            # Check if cache is still valid (1 hour TTL)
            cached_at = datetime.fromisoformat(cached["cached_at"])
            if (datetime.now() - cached_at).total_seconds() < 3600:
                return pd.DataFrame(cached["data"])
        
        return None
    
    def refresh_reaction_cluster_cache(self):
        """Refresh reaction cluster cache."""
        try:
            if self.storage.use_supabase:
                result = self.storage.supabase.table("reactions").select("reaction_normalized, cluster_id").execute()
                clusters = {}
                for row in result.data:
                    cluster_id = row.get("cluster_id")
                    if cluster_id:
                        if cluster_id not in clusters:
                            clusters[cluster_id] = []
                        clusters[cluster_id].append(row.get("reaction_normalized"))
                
                self.caches["reaction_cluster_cache"] = {
                    "data": clusters,
                    "cached_at": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error refreshing cluster cache: {str(e)}")
    
    def get_reaction_cluster(self, reaction: str) -> Optional[int]:
        """Get cluster ID for a reaction."""
        # Check cache
        clusters = self.caches["reaction_cluster_cache"].get("data", {})
        for cluster_id, reactions in clusters.items():
            if reaction in reactions:
                return cluster_id
        
        return None
    
    def refresh_drug_synonym_cache(self):
        """Refresh drug synonym cache."""
        try:
            if self.storage.use_supabase:
                result = self.storage.supabase.table("drugs").select("drug_normalized, synonyms").execute()
                synonyms = {}
                for row in result.data:
                    drug = row.get("drug_normalized")
                    syns = row.get("synonyms", [])
                    if syns:
                        synonyms[drug] = syns
                
                self.caches["drug_synonym_cache"] = {
                    "data": synonyms,
                    "cached_at": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error refreshing drug synonym cache: {str(e)}")
    
    def get_drug_synonyms(self, drug: str) -> List[str]:
        """Get synonyms for a drug."""
        synonyms = self.caches["drug_synonym_cache"].get("data", {})
        return synonyms.get(drug, [])

