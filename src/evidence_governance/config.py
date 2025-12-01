"""
Evidence Governance Configuration - Phase 3L Step 1
Configuration for evidence governance framework.
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Enable/disable evidence governance
EVIDENCE_GOVERNANCE_ENABLED = os.getenv("EVIDENCE_GOVERNANCE_ENABLED", "true").lower() == "true"

# Evidence Class definitions (weighted by reliability)
EVIDENCE_CLASSES = {
    "faers": 1.0,
    "eudra": 1.0,
    "vigibase": 1.0,
    "literature": 0.9,
    "clinical_trial": 0.9,
    "pubmed": 0.9,
    "dailymed": 0.85,
    "openfda": 0.85,
    "social": 0.6,
    "reddit": 0.6,
    "x": 0.6,
    "twitter": 0.6,
    "news": 0.5,
    "web": 0.4,
    "unknown": 0.3
}

# Quality scoring weights
QUALITY_WEIGHTS = {
    "completeness": 0.25,
    "source_reliability": 0.25,
    "recency": 0.20,
    "consistency": 0.20,
    "duplicate_penalty": -0.10
}

# Audit Trail Configuration
AUDIT_TRAIL_ENABLED = os.getenv("AUDIT_TRAIL_ENABLED", "true").lower() == "true"
AUDIT_LOG_DIR = Path("data/audit")
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit_events.jsonl"

# Lineage Configuration
LINEAGE_ENABLED = EVIDENCE_GOVERNANCE_ENABLED
LINEAGE_STORAGE = Path("data/lineage")

# Provenance Configuration
PROVENANCE_ENABLED = EVIDENCE_GOVERNANCE_ENABLED
PROVENANCE_STORAGE = Path("data/provenance")

# Fingerprint Configuration
FINGERPRINT_ALGORITHM = "sha256"  # sha256, sha512, md5 (not recommended)

# Data Quality Thresholds
QUALITY_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
    "low": 0.4,
    "poor": 0.0
}

# Regulatory Compliance Settings
REGULATORY_COMPLIANCE = {
    "21_cfr_part_11": True,
    "gdpr_compliant": True,
    "audit_retention_days": 2555,  # 7 years
    "immutable_logs": True,
    "cryptographic_verification": True
}


def ensure_directories():
    """Ensure all required directories exist."""
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    LINEAGE_STORAGE.mkdir(parents=True, exist_ok=True)
    PROVENANCE_STORAGE.mkdir(parents=True, exist_ok=True)


def get_evidence_class_weight(source: str) -> float:
    """
    Get evidence class weight for a source.
    
    Args:
        source: Source name
    
    Returns:
        Weight (0.0-1.0)
    """
    source_lower = source.lower()
    
    # Direct match
    if source_lower in EVIDENCE_CLASSES:
        return EVIDENCE_CLASSES[source_lower]
    
    # Partial match
    for evidence_class, weight in EVIDENCE_CLASSES.items():
        if evidence_class in source_lower:
            return weight
    
    # Default
    return EVIDENCE_CLASSES.get("unknown", 0.3)


def get_quality_threshold(score: float) -> str:
    """
    Get quality threshold category for a score.
    
    Args:
        score: Quality score (0.0-1.0)
    
    Returns:
        Threshold category
    """
    if score >= QUALITY_THRESHOLDS["high"]:
        return "high"
    elif score >= QUALITY_THRESHOLDS["medium"]:
        return "medium"
    elif score >= QUALITY_THRESHOLDS["low"]:
        return "low"
    else:
        return "poor"

