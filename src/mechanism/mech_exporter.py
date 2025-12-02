"""
Mechanistic Exporter - Export mechanistic analysis results
"""

import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

EXPORT_COLUMNS = [
    "drug", "reaction",
    "evidence_score", "fusion_score", "causal_score",
    "sources", "novel", "timestamp"
]


def normalize_for_export(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize entry for export.
    
    Args:
        entry: Mechanistic analysis entry
    
    Returns:
        Normalized dictionary
    """
    # Extract evidence score
    evidence = entry.get("evidence_score", {})
    if isinstance(evidence, dict):
        evidence_score = evidence.get("score", evidence.get("evidence_score", 0.0))
    else:
        evidence_score = float(evidence) if evidence else 0.0
    
    # Extract fusion score
    fusion = entry.get("fusion", {})
    fusion_score = fusion.get("fusion_score", 0.0) if isinstance(fusion, dict) else 0.0
    
    # Extract causal score
    causal = entry.get("causal", {})
    causal_score = causal.get("causal_score", 0.0) if isinstance(causal, dict) else 0.0
    
    # Extract sources
    sources = entry.get("sources", [])
    if not isinstance(sources, list):
        sources = []
    
    return {
        "drug": entry.get("drug", "Unknown"),
        "reaction": entry.get("reaction", "Unknown"),
        "evidence_score": evidence_score,
        "fusion_score": fusion_score,
        "causal_score": causal_score,
        "sources": ",".join(sources) if sources else "",
        "novel": entry.get("novel", False),
        "timestamp": entry.get("timestamp", datetime.now().isoformat()),
        "alert": entry.get("alert", {}).get("alert", False) if isinstance(entry.get("alert"), dict) else False,
        "alert_score": entry.get("alert", {}).get("alert_score", 0.0) if isinstance(entry.get("alert"), dict) else 0.0
    }


def export_json(entries: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """
    Export entries to JSON.
    
    Args:
        entries: List of mechanistic analysis entries
        filename: Optional output filename
    
    Returns:
        Output filename
    """
    filename = filename or f"mechanistic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        data = [normalize_for_export(e) for e in entries]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported {len(entries)} entries to {filename}")
        return filename
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        raise


def export_csv(entries: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """
    Export entries to CSV.
    
    Args:
        entries: List of mechanistic analysis entries
        filename: Optional output filename
    
    Returns:
        Output filename
    """
    filename = filename or f"mechanistic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        df = pd.DataFrame([normalize_for_export(e) for e in entries])
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(entries)} entries to {filename}")
        return filename
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise


def export_parquet(entries: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
    """
    Export entries to Parquet.
    
    Args:
        entries: List of mechanistic analysis entries
        filename: Optional output filename
    
    Returns:
        Output filename
    """
    filename = filename or f"mechanistic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    
    try:
        df = pd.DataFrame([normalize_for_export(e) for e in entries])
        df.to_parquet(filename, index=False)
        logger.info(f"Exported {len(entries)} entries to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Parquet export error: {e}")
        raise


def export_all_formats(entries: List[Dict[str, Any]], base_filename: Optional[str] = None) -> Dict[str, str]:
    """
    Export to all formats.
    
    Args:
        entries: List of mechanistic analysis entries
        base_filename: Optional base filename (without extension)
    
    Returns:
        Dictionary mapping format to filename
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = base_filename or f"mechanistic_export_{timestamp}"
    
    return {
        "json": export_json(entries, f"{base}.json"),
        "csv": export_csv(entries, f"{base}.csv"),
        "parquet": export_parquet(entries, f"{base}.parquet")
    }

