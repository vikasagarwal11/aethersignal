"""
Evidence Governance Engine - Phase 3L
Master orchestrator for evidence governance framework.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import logging

from .config import EVIDENCE_GOVERNANCE_ENABLED
from .lineage_tracker import LineageTracker
from .provenance import ProvenanceTracker
from .quality_scoring import QualityScorer
from .fingerprints import generate_fingerprint

logger = logging.getLogger(__name__)


class EvidenceGovernanceEngine:
    """
    Master orchestrator for evidence governance.
    Coordinates lineage, provenance, quality scoring, and fingerprinting.
    """
    
    def __init__(self):
        """Initialize evidence governance engine."""
        if not EVIDENCE_GOVERNANCE_ENABLED:
            logger.info("Evidence governance disabled")
            return
        
        self.lineage_tracker = LineageTracker()
        self.provenance_tracker = ProvenanceTracker()
        self.quality_scorer = QualityScorer()
    
    def process_record(
        self,
        record: Dict[str, Any],
        record_id: Optional[str] = None,
        source: Optional[str] = None,
        stage: str = "ingestion"
    ) -> Dict[str, Any]:
        """
        Process a record through the governance framework.
        
        Args:
            record: AE record dictionary
            record_id: Optional record ID (generated if not provided)
            source: Source name
            stage: Current transformation stage
        
        Returns:
            Enhanced record with governance metadata
        """
        if not EVIDENCE_GOVERNANCE_ENABLED:
            return record
        
        import uuid
        
        # Generate record ID if not provided
        if not record_id:
            record_id = record.get("ae_id") or record.get("id") or str(uuid.uuid4())
        
        # Get source
        source = source or record.get("source", "unknown")
        
        # Generate fingerprint
        fingerprint = generate_fingerprint(record)
        
        # Record lineage
        lineage_event = self.lineage_tracker.record(
            record_id=record_id,
            stage=stage,
            metadata={
                "source": source,
                "fingerprint": fingerprint
            }
        )
        
        # Record provenance
        provenance = self.provenance_tracker.record_provenance(
            record_id=record_id,
            source=source,
            platform=record.get("platform"),
            source_url=record.get("source_url"),
            source_id=record.get("source_id"),
            metadata=record.get("metadata")
        )
        
        # Calculate quality score
        quality_result = self.quality_scorer.score_record(record, source)
        
        # Add governance metadata to record
        record["governance"] = {
            "record_id": record_id,
            "fingerprint": fingerprint,
            "lineage_event_id": lineage_event.get("lineage_event_id"),
            "provenance_id": provenance.get("provenance_id"),
            "quality_score": quality_result["quality_score"],
            "quality_threshold": quality_result["threshold"],
            "quality_components": quality_result["components"]
        }
        
        return record
    
    def process_dataframe(
        self,
        df: pd.DataFrame,
        source_col: str = "source",
        stage: str = "ingestion"
    ) -> pd.DataFrame:
        """
        Process a DataFrame through the governance framework.
        
        Args:
            df: DataFrame with AE records
            source_col: Column name for source
            stage: Current transformation stage
        
        Returns:
            DataFrame with governance metadata columns added
        """
        if not EVIDENCE_GOVERNANCE_ENABLED or df.empty:
            return df
        
        processed_records = []
        
        for idx, row in df.iterrows():
            record = row.to_dict()
            source = record.get(source_col, "unknown")
            
            processed = self.process_record(record, source=source, stage=stage)
            processed_records.append(processed)
        
        # Convert back to DataFrame
        result_df = pd.DataFrame(processed_records)
        
        # Extract governance columns
        if "governance" in result_df.columns:
            governance_df = pd.json_normalize(result_df["governance"])
            result_df = pd.concat([result_df.drop(columns=["governance"]), governance_df], axis=1)
        
        return result_df
    
    def get_record_governance(self, record_id: str) -> Dict[str, Any]:
        """
        Get complete governance information for a record.
        
        Args:
            record_id: Record identifier
        
        Returns:
            Complete governance information
        """
        if not EVIDENCE_GOVERNANCE_ENABLED:
            return {}
        
        lineage = self.lineage_tracker.get_lineage_chain(record_id)
        provenance = self.provenance_tracker.get_provenance(record_id)
        
        return {
            "record_id": record_id,
            "lineage": lineage,
            "provenance": provenance
        }
    
    def get_quality_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get quality score summary for a DataFrame.
        
        Args:
            df: DataFrame with quality_score column
        
        Returns:
            Quality summary statistics
        """
        if df.empty or "quality_score" not in df.columns:
            return {}
        
        return {
            "mean_quality": df["quality_score"].mean(),
            "median_quality": df["quality_score"].median(),
            "high_quality_count": len(df[df["quality_score"] >= 0.8]),
            "medium_quality_count": len(df[(df["quality_score"] >= 0.6) & (df["quality_score"] < 0.8)]),
            "low_quality_count": len(df[df["quality_score"] < 0.6]),
            "total_records": len(df)
        }

