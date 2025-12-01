"""
Schema Migrator - Migrates existing data to unified schema
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging

from .unified_storage import UnifiedStorageEngine
from src.normalization.reaction_normalizer import ReactionNormalizer
from src.social_ae.reaction_embeddings import ReactionEmbeddingEngine

logger = logging.getLogger(__name__)


class SchemaMigrator:
    """
    Migrates existing data to unified schema.
    """
    
    def __init__(self, storage: UnifiedStorageEngine):
        """
        Initialize schema migrator.
        
        Args:
            storage: Unified storage engine
        """
        self.storage = storage
        self.normalizer = ReactionNormalizer()
        self.embedding_engine = ReactionEmbeddingEngine()
    
    def migrate_from_ae_records(
        self,
        df: pd.DataFrame
    ) -> int:
        """
        Migrate from existing ae_records table to unified schema.
        
        Args:
            df: DataFrame from existing ae_records table
        
        Returns:
            Number of records migrated
        """
        if df.empty:
            return 0
        
        migrated = 0
        
        for _, row in df.iterrows():
            try:
                # Map to unified schema
                event = {
                    "ae_id": str(row.get("id", "")),
                    "source": row.get("source", "unknown"),
                    "drug_raw": row.get("drug", ""),
                    "drug_normalized": self._normalize_drug(row.get("drug", "")),
                    "reaction_raw": row.get("reaction", ""),
                    "reaction_normalized": self._normalize_reaction(row.get("reaction", "")),
                    "confidence": float(row.get("confidence", 0.0)) if pd.notna(row.get("confidence")) else 0.0,
                    "severity": float(row.get("severity", 0.0)) if pd.notna(row.get("severity")) else 0.0,
                    "full_text": str(row.get("text", ""))[:5000],
                    "text_snippet": str(row.get("text", ""))[:500],
                    "event_date": self._parse_date(row.get("timestamp")),
                    "metadata": self._parse_metadata(row.get("metadata", {}))
                }
                
                # Generate embedding
                text = event.get("full_text", "")
                embedding = self.embedding_engine.embed(text) if text else None
                
                # Store
                self.storage.store_ae_event(event, embedding)
                migrated += 1
            except Exception as e:
                logger.warning(f"Error migrating record: {str(e)}")
                continue
        
        return migrated
    
    def _normalize_drug(self, drug: str) -> str:
        """Normalize drug name."""
        if not drug or pd.isna(drug):
            return ""
        return str(drug).lower().strip()
    
    def _normalize_reaction(self, reaction: str) -> str:
        """Normalize reaction using ReactionNormalizer."""
        if not reaction or pd.isna(reaction):
            return ""
        
        normalized = self.normalizer.normalize(str(reaction))
        return normalized.get("pt", str(reaction).title())
    
    def _parse_date(self, date_value) -> Optional[str]:
        """Parse date value."""
        if pd.isna(date_value) or not date_value:
            return None
        
        try:
            if isinstance(date_value, str):
                # Try to parse
                from datetime import datetime
                return datetime.fromisoformat(date_value.replace("Z", "+00:00")).isoformat()
            elif isinstance(date_value, datetime):
                return date_value.isoformat()
        except Exception:
            pass
        
        return None
    
    def _parse_metadata(self, metadata) -> Dict[str, Any]:
        """Parse metadata."""
        if isinstance(metadata, dict):
            return metadata
        elif isinstance(metadata, str):
            try:
                import json
                return json.loads(metadata)
            except Exception:
                return {}
        else:
            return {}

