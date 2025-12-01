"""
Provenance Engine - Phase 3L Step 3
Evidence class system, source trust scoring, recency, processing stage scoring, SHA-256 fingerprints.
"""

import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .config import EVIDENCE_CLASSES, get_evidence_class_weight

logger = logging.getLogger(__name__)


class ProvenanceEngine:
    """
    Provenance Engine - Calculates trust scores for AE records.
    
    Features:
    - Evidence class classification
    - Source trust scoring
    - Recency/freshness scoring
    - Processing stage scoring
    - Schema completeness scoring
    - SHA-256 integrity fingerprints
    - Final provenance score (0-100)
    """
    
    def __init__(self):
        """Initialize provenance engine with source weights."""
        # Source trust weights (regulatory > scientific > patient-reported)
        self.source_weights = {
            "faers": 0.95,
            "eudravigilance": 0.92,
            "eudra": 0.92,
            "openfda": 0.90,
            "pubmed": 0.88,
            "clinicaltrials": 0.85,
            "clinical_trials": 0.85,
            "dailymed": 0.87,
            "ema_prac": 0.90,
            "yellowcard": 0.88,
            "health_canada": 0.88,
            "reddit": 0.70,
            "social_reddit": 0.70,
            "twitter": 0.60,
            "x": 0.60,
            "social_x": 0.60,
            "tiktok": 0.50,
            "forum": 0.65,
            "google_places": 0.55,
            "unknown": 0.40,
        }
        
        # Evidence classes (from config)
        self.evidence_classes = EVIDENCE_CLASSES
    
    def make_hash(self, record: Dict[str, Any]) -> str:
        """
        Generate SHA-256 fingerprint for record integrity.
        
        Args:
            record: AE record dictionary
        
        Returns:
            SHA-256 hex digest
        """
        try:
            # Create deterministic string representation
            record_str = str(sorted(record.items()))
            h = hashlib.sha256(record_str.encode("utf-8")).hexdigest()
            return h
        except Exception as e:
            logger.error(f"Error generating hash: {e}")
            return ""
    
    def classify_evidence(self, source: str) -> str:
        """
        Classify evidence into regulatory categories.
        
        Args:
            source: Source name
        
        Returns:
            Evidence class name
        """
        source_lower = source.lower()
        
        # Regulatory sources
        if source_lower in ["faers", "eudravigilance", "eudra", "openfda", "ema_prac", "yellowcard", "health_canada"]:
            return "Regulatory"
        
        # Scientific sources
        if source_lower in ["pubmed", "clinicaltrials", "clinical_trials", "dailymed"]:
            return "Scientific"
        
        # Patient-reported sources
        if source_lower in ["reddit", "social_reddit", "twitter", "x", "social_x", "forum"]:
            return "Patient-Reported"
        
        # Unstructured sources
        if source_lower in ["tiktok", "google_places"]:
            return "Unstructured"
        
        return "Unknown"
    
    def calculate_recency_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate recency score (newer = higher trust).
        
        Args:
            record: AE record
        
        Returns:
            Recency score (0-1)
        """
        try:
            created_date = record.get("created_date") or record.get("timestamp") or record.get("date")
            
            if not created_date:
                return 0.5  # Default moderate
            
            # Parse date
            if isinstance(created_date, str):
                try:
                    created_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
                except:
                    try:
                        created_date = datetime.strptime(created_date, "%Y-%m-%d")
                    except:
                        return 0.5
            
            if isinstance(created_date, datetime):
                age_days = (datetime.now() - created_date.replace(tzinfo=None)).days
            else:
                return 0.5
            
            # Score: 1.0 for today, 0.8 for 7 days, 0.5 for 30 days, 0.2 for 90 days
            if age_days <= 1:
                return 1.0
            elif age_days <= 7:
                return 0.9
            elif age_days <= 30:
                return 0.7
            elif age_days <= 90:
                return 0.5
            elif age_days <= 180:
                return 0.3
            else:
                return 0.1
        except Exception:
            return 0.5
    
    def calculate_completeness_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate schema completeness score.
        
        Args:
            record: AE record
        
        Returns:
            Completeness score (0-1)
        """
        expected_fields = [
            "drug", "reaction", "created_date", "source",
            "text", "confidence", "record_id"
        ]
        
        present = sum(1 for f in expected_fields if record.get(f) not in [None, "", []])
        score = present / len(expected_fields) if expected_fields else 1.0
        
        return round(min(score, 1.0), 2)
    
    def calculate_processing_score(self, lineage_chain: List[Dict[str, Any]]) -> float:
        """
        Calculate processing stage score (more stages = more validated).
        
        Args:
            lineage_chain: List of lineage events
        
        Returns:
            Processing score (0-1)
        """
        if not lineage_chain:
            return 0.3  # Low if no lineage
        
        stages = len(lineage_chain)
        
        # More stages = better validation
        if stages >= 5:
            return 1.0
        elif stages >= 3:
            return 0.8
        elif stages >= 2:
            return 0.6
        else:
            return 0.4
    
    def score(
        self,
        record: Dict[str, Any],
        lineage_chain: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete provenance score for a record.
        
        Args:
            record: AE record dictionary
            lineage_chain: Optional lineage chain (if not provided, will be empty)
        
        Returns:
            Provenance score dictionary
        """
        if lineage_chain is None:
            lineage_chain = []
        
        source = record.get("source", "unknown")
        evidence_class = self.classify_evidence(source)
        evidence_class_weight = get_evidence_class_weight(evidence_class)
        
        # Calculate component scores
        source_score = self.source_weights.get(source.lower(), 0.40)
        recency_score = self.calculate_recency_score(record)
        completeness_score = self.calculate_completeness_score(record)
        processing_score = self.calculate_processing_score(lineage_chain)
        
        # Final weighted score (0-1, then convert to 0-100)
        final_score = (
            0.40 * source_score +
            0.20 * completeness_score +
            0.20 * processing_score +
            0.20 * recency_score
        )
        
        # Generate fingerprint
        fingerprint = self.make_hash(record)
        
        return {
            "record_id": record.get("record_id") or record.get("ae_id"),
            "evidence_class": evidence_class,
            "evidence_class_weight": evidence_class_weight,
            "source_score": round(source_score, 2),
            "completeness_score": completeness_score,
            "processing_score": processing_score,
            "recency_score": round(recency_score, 2),
            "final_provenance_score": round(final_score * 100, 2),
            "fingerprint_sha256": fingerprint
        }

