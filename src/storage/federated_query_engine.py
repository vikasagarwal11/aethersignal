"""
Federated Query Engine (Phase 3A.5)
Single query interface for ALL sources with natural language support.
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import re

from .unified_storage import UnifiedStorageEngine
from src.normalization.reaction_normalizer import ReactionNormalizer
from src.social_ae.reaction_embeddings import ReactionEmbeddingEngine

logger = logging.getLogger(__name__)


class FederatedQueryEngine:
    """
    Federated query engine that provides unified querying across all sources.
    """
    
    def __init__(
        self,
        storage: Optional[UnifiedStorageEngine] = None,
        normalizer: Optional[ReactionNormalizer] = None,
        embedding_engine: Optional[ReactionEmbeddingEngine] = None
    ):
        """
        Initialize federated query engine.
        
        Args:
            storage: Unified storage engine
            normalizer: Reaction normalizer
            embedding_engine: Embedding engine for semantic search
        """
        self.storage = storage or UnifiedStorageEngine()
        self.normalizer = normalizer or ReactionNormalizer()
        self.embedding_engine = embedding_engine or ReactionEmbeddingEngine()
    
    def query(
        self,
        query_text: Optional[str] = None,
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        sources: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        severity_min: Optional[float] = None,
        quantum_score_min: Optional[float] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Execute federated query across all sources.
        
        Args:
            query_text: Natural language query (e.g., "tachycardia cases for semaglutide")
            drug: Drug name filter
            reaction: Reaction filter
            sources: List of sources to query
            date_range: Tuple of (start_date, end_date)
            severity_min: Minimum severity score
            quantum_score_min: Minimum quantum score
            limit: Maximum results
        
        Returns:
            DataFrame with unified AE events
        """
        # Parse natural language query if provided
        if query_text:
            parsed = self._parse_natural_language_query(query_text)
            drug = drug or parsed.get("drug")
            reaction = reaction or parsed.get("reaction")
            sources = sources or parsed.get("sources")
            date_range = date_range or parsed.get("date_range")
        
        # Normalize drug and reaction
        if drug:
            drug_normalized = self._normalize_drug(drug)
        else:
            drug_normalized = None
        
        if reaction:
            normalized = self.normalizer.normalize(reaction, drug)
            reaction_normalized = normalized["pt"]
        else:
            reaction_normalized = None
        
        # Build SQL query
        query, params = self._build_query(
            drug_normalized=drug_normalized,
            reaction_normalized=reaction_normalized,
            sources=sources,
            date_range=date_range,
            severity_min=severity_min,
            quantum_score_min=quantum_score_min,
            limit=limit
        )
        
        # Execute query
        if self.storage.use_supabase:
            return self._execute_supabase_query(query, params)
        else:
            return self._execute_sqlite_query(query, params)
    
    def _parse_natural_language_query(self, query_text: str) -> Dict[str, Any]:
        """
        Parse natural language query.
        
        Examples:
        - "tachycardia cases for semaglutide"
        - "show me all nausea events from last 30 days"
        - "serious events for GLP-1 drugs"
        """
        parsed = {
            "drug": None,
            "reaction": None,
            "sources": None,
            "date_range": None
        }
        
        query_lower = query_text.lower()
        
        # Extract drug names (common drugs)
        common_drugs = ["semaglutide", "ozempic", "wegovy", "mounjaro", "tirzepatide", 
                        "liraglutide", "dulaglutide", "metformin", "insulin"]
        for drug in common_drugs:
            if drug in query_lower:
                parsed["drug"] = drug
                break
        
        # Extract reactions (common reactions)
        common_reactions = ["nausea", "vomiting", "diarrhea", "headache", "tachycardia",
                           "palpitations", "rash", "fatigue", "dizziness"]
        for reaction in common_reactions:
            if reaction in query_lower:
                parsed["reaction"] = reaction
                break
        
        # Extract time references
        if "last 30 days" in query_lower or "past month" in query_lower:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            parsed["date_range"] = (start_date, end_date)
        elif "last 7 days" in query_lower or "past week" in query_lower:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            parsed["date_range"] = (start_date, end_date)
        
        # Extract source references
        if "social" in query_lower or "reddit" in query_lower:
            parsed["sources"] = ["social", "reddit", "x"]
        elif "faers" in query_lower or "fda" in query_lower:
            parsed["sources"] = ["faers", "openfda"]
        elif "literature" in query_lower or "pubmed" in query_lower:
            parsed["sources"] = ["pubmed", "literature"]
        
        return parsed
    
    def _normalize_drug(self, drug: str) -> str:
        """Normalize drug name."""
        # Simple normalization (would use drug dictionary in production)
        return drug.lower().strip()
    
    def _build_query(
        self,
        drug_normalized: Optional[str] = None,
        reaction_normalized: Optional[str] = None,
        sources: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        severity_min: Optional[float] = None,
        quantum_score_min: Optional[float] = None,
        limit: int = 1000
    ) -> Tuple[str, List[Any]]:
        """Build SQL query."""
        query = "SELECT * FROM ae_events WHERE 1=1"
        params = []
        
        if drug_normalized:
            query += " AND drug_normalized = ?"
            params.append(drug_normalized)
        
        if reaction_normalized:
            query += " AND reaction_normalized = ?"
            params.append(reaction_normalized)
        
        if sources:
            placeholders = ", ".join(["?" for _ in sources])
            query += f" AND source IN ({placeholders})"
            params.extend(sources)
        
        if date_range:
            start_date, end_date = date_range
            query += " AND event_date >= ? AND event_date <= ?"
            params.append(start_date.isoformat())
            params.append(end_date.isoformat())
        
        if severity_min is not None:
            query += " AND reaction_severity_score >= ?"
            params.append(severity_min)
        
        if quantum_score_min is not None:
            query += " AND quantum_score >= ?"
            params.append(quantum_score_min)
        
        query += " ORDER BY quantum_score DESC, event_date DESC LIMIT ?"
        params.append(limit)
        
        return query, params
    
    def _execute_supabase_query(self, query: str, params: List[Any]) -> pd.DataFrame:
        """Execute query on Supabase."""
        try:
            # Supabase uses different query syntax
            # For now, use table().select() API
            result = self.storage.supabase.table("ae_events").select("*").limit(1000).execute()
            
            df = pd.DataFrame(result.data)
            return df
        except Exception as e:
            logger.error(f"Error executing Supabase query: {str(e)}")
            return pd.DataFrame()
    
    def _execute_sqlite_query(self, query: str, params: List[Any]) -> pd.DataFrame:
        """Execute query on SQLite."""
        try:
            conn = sqlite3.connect(self.storage.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse JSON fields
            for field in ["seriousness_flags", "metadata"]:
                if field in df.columns:
                    df[field] = df[field].apply(
                        lambda x: json.loads(x) if isinstance(x, str) and x.startswith("{") else {}
                    )
            
            return df
        except Exception as e:
            logger.error(f"Error executing SQLite query: {str(e)}")
            return pd.DataFrame()
    
    def semantic_search(
        self,
        query_text: str,
        drug: Optional[str] = None,
        k: int = 10
    ) -> pd.DataFrame:
        """
        Semantic search using embeddings.
        
        Args:
            query_text: Search query
            drug: Optional drug filter
            k: Number of results
        
        Returns:
            DataFrame with similar AE events
        """
        # Generate embedding for query
        embedding = self.embedding_engine.embed(query_text)
        if embedding is None:
            return pd.DataFrame()
        
        # Use vector similarity search
        if self.storage.use_supabase:
            try:
                # Use Supabase RPC function
                result = self.storage.supabase.rpc(
                    "find_similar_reactions",
                    {
                        "query_embedding": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                        "match_count": k,
                        "drug_filter": drug
                    }
                ).execute()
                
                return pd.DataFrame(result.data)
            except Exception as e:
                logger.error(f"Error in semantic search: {str(e)}")
                return pd.DataFrame()
        else:
            # SQLite doesn't support vector search natively
            # Fallback to keyword search
            return self.query(query_text=query_text, drug=drug, limit=k)
    
    def get_drug_reaction_summary(
        self,
        drug: str,
        reaction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Optional reaction filter
        
        Returns:
            Dictionary with summary statistics
        """
        df = self.query(drug=drug, reaction=reaction, limit=10000)
        
        if df.empty:
            return {
                "total_cases": 0,
                "sources": [],
                "avg_quantum_score": 0.0,
                "avg_severity": 0.0
            }
        
        return {
            "total_cases": len(df),
            "sources": df["source"].unique().tolist() if "source" in df.columns else [],
            "source_count": df["source"].nunique() if "source" in df.columns else 0,
            "avg_quantum_score": df["quantum_score"].mean() if "quantum_score" in df.columns else 0.0,
            "avg_severity": df["reaction_severity_score"].mean() if "reaction_severity_score" in df.columns else 0.0,
            "first_event": df["event_date"].min() if "event_date" in df.columns else None,
            "last_event": df["event_date"].max() if "event_date" in df.columns else None
        }
    
    def get_cross_source_breakdown(
        self,
        drug: str,
        reaction: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get breakdown by source.
        
        Args:
            drug: Drug name
            reaction: Optional reaction filter
        
        Returns:
            DataFrame with source breakdown
        """
        df = self.query(drug=drug, reaction=reaction, limit=10000)
        
        if df.empty or "source" not in df.columns:
            return pd.DataFrame()
        
        breakdown = df.groupby("source").agg({
            "ae_id": "count",
            "quantum_score": "mean",
            "reaction_severity_score": "mean",
            "consensus_score": "mean"
        }).reset_index()
        
        breakdown.columns = ["source", "case_count", "avg_quantum_score", "avg_severity", "avg_consensus"]
        
        return breakdown

