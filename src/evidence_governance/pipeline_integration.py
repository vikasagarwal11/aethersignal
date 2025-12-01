"""
Pipeline Integration Hooks - Phase 3L Step 2
Comprehensive lineage tracking integration across all pipelines.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from .lineage import get_lineage_tracker
from .config import EVIDENCE_GOVERNANCE_ENABLED

logger = logging.getLogger(__name__)


def track_faers_ingestion(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track FAERS record ingestion.
    
    Args:
        record: FAERS record dictionary
    
    Returns:
        Record with lineage tracking
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return record
    
    try:
        lineage = get_lineage_tracker()
        record_id = record.get("primaryid") or record.get("caseid") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "ingestion",
            {
                "source": "faers",
                "primaryid": record.get("primaryid"),
                "caseid": record.get("caseid")
            }
        )
        
        record["_lineage_id"] = record_id
    except Exception as e:
        logger.debug(f"Lineage tracking error: {e}")
    
    return record


def track_faers_cleaning(record: Dict[str, Any]) -> Dict[str, Any]:
    """Track FAERS record cleaning."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return record
    
    try:
        lineage = get_lineage_tracker()
        record_id = record.get("_lineage_id") or record.get("primaryid") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "cleaning",
            {
                "source": "faers",
                "fields_cleaned": list(record.keys())
            }
        )
    except Exception:
        pass
    
    return record


def track_faers_mapping(record: Dict[str, Any]) -> Dict[str, Any]:
    """Track FAERS record mapping to unified schema."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return record
    
    try:
        lineage = get_lineage_tracker()
        record_id = record.get("_lineage_id") or record.get("primaryid") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "mapping",
            {
                "source": "faers",
                "schema": "unified",
                "drug": record.get("drug"),
                "reaction": record.get("reaction")
            }
        )
    except Exception:
        pass
    
    return record


def track_social_ingestion(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track social post ingestion.
    
    Args:
        post: Social post dictionary
    
    Returns:
        Post with lineage tracking
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return post
    
    try:
        lineage = get_lineage_tracker()
        record_id = post.get("post_id") or post.get("id") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "ingestion",
            {
                "source": "social",
                "platform": post.get("platform", "unknown"),
                "post_id": record_id
            }
        )
        
        post["_lineage_id"] = record_id
    except Exception as e:
        logger.debug(f"Lineage tracking error: {e}")
    
    return post


def track_social_cleaning(post: Dict[str, Any]) -> Dict[str, Any]:
    """Track social post cleaning."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return post
    
    try:
        lineage = get_lineage_tracker()
        record_id = post.get("_lineage_id") or post.get("post_id") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "cleaning",
            {
                "source": "social",
                "platform": post.get("platform"),
                "text_length": len(post.get("text", ""))
            }
        )
    except Exception:
        pass
    
    return post


def track_social_normalization(post: Dict[str, Any]) -> Dict[str, Any]:
    """Track social post normalization."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return post
    
    try:
        lineage = get_lineage_tracker()
        record_id = post.get("_lineage_id") or post.get("post_id") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "normalization",
            {
                "source": "social",
                "drug": post.get("drug"),
                "reactions_count": len(post.get("reactions", [])) if isinstance(post.get("reactions"), list) else 0
            }
        )
    except Exception:
        pass
    
    return post


def track_social_reaction_extraction(post: Dict[str, Any]) -> Dict[str, Any]:
    """Track social post reaction extraction."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return post
    
    try:
        lineage = get_lineage_tracker()
        record_id = post.get("_lineage_id") or post.get("post_id") or str(uuid.uuid4())
        
        reactions = post.get("reactions", [])
        if isinstance(reactions, str):
            reactions = [reactions]
        
        lineage.record(
            record_id,
            "mapping",
            {
                "source": "social",
                "reactions_extracted": len(reactions),
                "reactions": reactions[:5]  # First 5 for metadata
            }
        )
    except Exception:
        pass
    
    return post


def track_literature_ingestion(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track literature document ingestion.
    
    Args:
        doc: Literature document dictionary
    
    Returns:
        Document with lineage tracking
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return doc
    
    try:
        lineage = get_lineage_tracker()
        record_id = doc.get("pmid") or doc.get("id") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "ingestion",
            {
                "source": "literature",
                "pmid": doc.get("pmid"),
                "title": doc.get("title", "")[:100]
            }
        )
        
        doc["_lineage_id"] = record_id
    except Exception as e:
        logger.debug(f"Lineage tracking error: {e}")
    
    return doc


def track_literature_parsing(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Track literature text parsing."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return doc
    
    try:
        lineage = get_lineage_tracker()
        record_id = doc.get("_lineage_id") or doc.get("pmid") or str(uuid.uuid4())
        
        text = doc.get("text", "") or doc.get("abstract", "")
        
        lineage.record(
            record_id,
            "cleaning",
            {
                "source": "literature",
                "text_length": len(text),
                "tokens": len(text.split()) if text else 0
            }
        )
    except Exception:
        pass
    
    return doc


def track_literature_ae_extraction(doc: Dict[str, Any], extracted_ae: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Track literature AE extraction."""
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return doc
    
    try:
        lineage = get_lineage_tracker()
        record_id = doc.get("_lineage_id") or doc.get("pmid") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "mapping",
            {
                "source": "literature",
                "ae_count": len(extracted_ae),
                "ae_list": [ae.get("reaction", "") for ae in extracted_ae[:5]]
            }
        )
    except Exception:
        pass
    
    return doc


def track_datasource_fetch(source_name: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Track data source fetch.
    
    Args:
        source_name: Source name
        records: List of records fetched
    
    Returns:
        Records with lineage tracking
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return records
    
    try:
        lineage = get_lineage_tracker()
        
        for record in records:
            record_id = (
                record.get("record_id") or
                record.get("id") or
                record.get("primaryid") or
                str(uuid.uuid4())
            )
            
            lineage.record(
                record_id,
                "ingestion",
                {
                    "source": source_name,
                    "fetch_timestamp": record.get("timestamp")
                }
            )
            
            record["_lineage_id"] = record_id
    except Exception as e:
        logger.debug(f"Lineage tracking error: {e}")
    
    return records


def track_scoring(record: Dict[str, Any], scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Track score calculation.
    
    Args:
        record: AE record
        scores: Dictionary with calculated scores
    
    Returns:
        Record with scores
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return record
    
    try:
        lineage = get_lineage_tracker()
        record_id = record.get("_lineage_id") or record.get("ae_id") or str(uuid.uuid4())
        
        lineage.record(
            record_id,
            "scoring",
            {
                "quantum_score": scores.get("quantum_score"),
                "severity_score": scores.get("severity_score"),
                "confidence": scores.get("confidence")
            }
        )
    except Exception:
        pass
    
    return record


def track_aggregation(record_ids: List[str], aggregation_type: str) -> Dict[str, Any]:
    """
    Track aggregation for dashboard.
    
    Args:
        record_ids: List of record IDs being aggregated
        aggregation_type: Type of aggregation (kpi, trend, signal_ranking, etc.)
    
    Returns:
        Aggregation metadata
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return {}
    
    try:
        lineage = get_lineage_tracker()
        
        # Record aggregation event for each record
        for record_id in record_ids[:100]:  # Limit to first 100 to avoid spam
            lineage.record(
                record_id,
                "aggregation",
                {
                    "aggregation_type": aggregation_type,
                    "record_count": len(record_ids)
                }
            )
    except Exception:
        pass
    
    return {"aggregation_type": aggregation_type, "record_count": len(record_ids)}


def track_visualization(record_ids: List[str], visualization_type: str) -> Dict[str, Any]:
    """
    Track visualization rendering.
    
    Args:
        record_ids: List of record IDs being visualized
        visualization_type: Type of visualization (chart, table, heatmap, etc.)
    
    Returns:
        Visualization metadata
    """
    if not EVIDENCE_GOVERNANCE_ENABLED:
        return {}
    
    try:
        lineage = get_lineage_tracker()
        
        # Record visualization event for each record (limited)
        for record_id in record_ids[:50]:  # Limit to avoid spam
            lineage.record(
                record_id,
                "visualization",
                {
                    "visualization_type": visualization_type
                }
            )
    except Exception:
        pass
    
    return {"visualization_type": visualization_type, "record_count": len(record_ids)}

