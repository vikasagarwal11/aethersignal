"""
Fingerprints - Phase 3L Step 1
Cryptographic fingerprinting for evidence integrity.
"""

import hashlib
import json
from typing import Dict, Any, Optional
import logging

from .config import FINGERPRINT_ALGORITHM

logger = logging.getLogger(__name__)


def generate_fingerprint(record: Dict[str, Any], algorithm: Optional[str] = None) -> str:
    """
    Generate cryptographic fingerprint for a record.
    
    Args:
        record: Record dictionary
        algorithm: Hash algorithm (sha256, sha512, md5)
    
    Returns:
        Hexadecimal fingerprint string
    """
    algorithm = algorithm or FINGERPRINT_ALGORITHM
    
    # Normalize record (sort keys, convert to JSON)
    normalized = json.dumps(record, sort_keys=True, default=str)
    
    # Generate hash
    if algorithm == "sha256":
        hash_obj = hashlib.sha256()
    elif algorithm == "sha512":
        hash_obj = hashlib.sha512()
    elif algorithm == "md5":
        hash_obj = hashlib.md5()
    else:
        logger.warning(f"Unknown algorithm: {algorithm}, using sha256")
        hash_obj = hashlib.sha256()
    
    hash_obj.update(normalized.encode("utf-8"))
    return hash_obj.hexdigest()


def verify_fingerprint(record: Dict[str, Any], expected_fingerprint: str, algorithm: Optional[str] = None) -> bool:
    """
    Verify record fingerprint.
    
    Args:
        record: Record dictionary
        expected_fingerprint: Expected fingerprint
        algorithm: Hash algorithm
    
    Returns:
        True if fingerprint matches
    """
    actual = generate_fingerprint(record, algorithm)
    return actual == expected_fingerprint


def generate_batch_fingerprints(records: list[Dict[str, Any]], algorithm: Optional[str] = None) -> Dict[str, str]:
    """
    Generate fingerprints for multiple records.
    
    Args:
        records: List of record dictionaries
        algorithm: Hash algorithm
    
    Returns:
        Dictionary mapping record index to fingerprint
    """
    fingerprints = {}
    
    for idx, record in enumerate(records):
        fingerprints[str(idx)] = generate_fingerprint(record, algorithm)
    
    return fingerprints

