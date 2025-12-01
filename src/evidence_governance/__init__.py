"""
Evidence Governance Module - Phase 3L
Ensures traceability, lineage, data quality, and regulatory compliance.
"""

from .governance_engine import EvidenceGovernanceEngine
from .lineage_tracker import LineageTracker
from .quality_scoring import QualityScorer
from .provenance import ProvenanceTracker, get_provenance_engine, get_provenance_tracker
from .provenance_engine import ProvenanceEngine
from .quality_engine import DataQualityEngine
from .quality import get_quality_engine
from .fusion_engine import EvidenceFusionEngine
from .fusion import get_fusion_engine
from .fingerprints import generate_fingerprint
from .lineage import get_lineage_tracker, record_lineage
from .pipeline_integration import (
    track_faers_ingestion,
    track_faers_cleaning,
    track_faers_mapping,
    track_social_ingestion,
    track_social_cleaning,
    track_social_normalization,
    track_social_reaction_extraction,
    track_literature_ingestion,
    track_literature_parsing,
    track_literature_ae_extraction,
    track_datasource_fetch,
    track_scoring,
    track_aggregation,
    track_visualization
)

__all__ = [
    "EvidenceGovernanceEngine",
    "LineageTracker",
    "QualityScorer",
    "ProvenanceTracker",
    "ProvenanceEngine",
    "DataQualityEngine",
    "EvidenceFusionEngine",
    "get_provenance_engine",
    "get_provenance_tracker",
    "get_quality_engine",
    "get_fusion_engine",
    "generate_fingerprint",
    "get_lineage_tracker",
    "record_lineage",
    "track_faers_ingestion",
    "track_faers_cleaning",
    "track_faers_mapping",
    "track_social_ingestion",
    "track_social_cleaning",
    "track_social_normalization",
    "track_social_reaction_extraction",
    "track_literature_ingestion",
    "track_literature_parsing",
    "track_literature_ae_extraction",
    "track_datasource_fetch",
    "track_scoring",
    "track_aggregation",
    "track_visualization"
]
