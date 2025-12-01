"""
Evidence Governance Integration - Phase 3L Step 2
Integration hooks for lineage tracking across all pipelines.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

from .governance_engine import EvidenceGovernanceEngine
from .config import EVIDENCE_GOVERNANCE_ENABLED

logger = logging.getLogger(__name__)

# Global governance engine instance
_governance_engine: Optional[EvidenceGovernanceEngine] = None


def get_governance_engine() -> Optional[EvidenceGovernanceEngine]:
    """Get or create global governance engine instance."""
    global _governance_engine
    
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return None
    
    if _governance_engine is None:
        _governance_engine = EvidenceGovernanceEngine()
    
    return _governance_engine


def track_ingestion(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Track record ingestion.
    
    Args:
        record: AE record
        source: Source name
    
    Returns:
        Record with governance metadata
    """
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="ingestion")


def track_cleaning(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Track record cleaning."""
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="cleaning")


def track_normalization(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Track record normalization."""
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="normalization")


def track_mapping(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Track record mapping to unified schema."""
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="mapping")


def track_scoring(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Track score calculation."""
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="scoring")


def track_storage(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Track record storage."""
    engine = get_governance_engine()
    if not engine:
        return record
    
    return engine.process_record(record, source=source, stage="storage")


def track_aggregation(df: pd.DataFrame, source_col: str = "source") -> pd.DataFrame:
    """Track aggregation for dashboard."""
    engine = get_governance_engine()
    if not engine:
        return df
    
    return engine.process_dataframe(df, source_col=source_col, stage="aggregation")


def track_visualization(df: pd.DataFrame, source_col: str = "source") -> pd.DataFrame:
    """Track visualization rendering."""
    engine = get_governance_engine()
    if not engine:
        return df
    
    return engine.process_dataframe(df, source_col=source_col, stage="visualization")


def integrate_with_pipeline(df: pd.DataFrame, source: str, stage: str) -> pd.DataFrame:
    """
    Integrate governance tracking into any pipeline stage.
    
    Args:
        df: DataFrame to process
        source: Source name
        stage: Transformation stage
    
    Returns:
        DataFrame with governance metadata
    """
    engine = get_governance_engine()
    if not engine:
        return df
    
    return engine.process_dataframe(df, source_col="source", stage=stage)

