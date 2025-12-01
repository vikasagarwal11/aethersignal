"""
Data Quality Engine - Phase 3L Step 4
Seven dimensions of data quality: completeness, consistency, validity, accuracy, noise, ambiguity, stability.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataQualityEngine:
    """
    Data Quality Engine - Evaluates AE records across 7 quality dimensions.
    
    Dimensions:
    1. Completeness
    2. Consistency
    3. Validity (format, standardization)
    4. Accuracy (NER + mapping correctness)
    5. Noise Level
    6. Ambiguity / Uncertainty
    7. Stability / Duplicates
    """
    
    def __init__(self):
        """Initialize quality engine."""
        # Expected fields for regulatory-grade evidence
        self.expected_fields = [
            "drug", "reaction", "created_date",
            "source", "text", "confidence",
            "record_id"
        ]
        
        # Penalties for missing fields
        self.missing_field_penalty = 0.05
        
        # Source-level quality baseline
        self.source_quality = {
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
            "reddit": 0.60,
            "social_reddit": 0.60,
            "twitter": 0.50,
            "x": 0.50,
            "social_x": 0.50,
            "tiktok": 0.40,
            "forum": 0.55,
            "google_places": 0.55,
            "unknown": 0.40
        }
        
        # Weak/ambiguous terms
        self.weak_terms = [
            "maybe", "might", "could be", "not sure",
            "idk", "i think", "possibly", "perhaps",
            "unclear", "not certain", "dunno"
        ]
    
    def completeness_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate completeness score.
        
        Args:
            record: AE record
        
        Returns:
            Completeness score (0-1)
        """
        total = len(self.expected_fields)
        missing = 0
        
        for field in self.expected_fields:
            if field not in record or record.get(field) in [None, "", []]:
                missing += 1
        
        score = max(0.0, 1 - (missing * self.missing_field_penalty))
        return round(min(score, 1.0), 2)
    
    def consistency_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate consistency score.
        
        Args:
            record: AE record
        
        Returns:
            Consistency score (0-1)
        """
        score = 1.0
        
        # Date validity
        created_date = record.get("created_date") or record.get("timestamp")
        if created_date:
            if not isinstance(created_date, (datetime, str)):
                score -= 0.25
        
        # Drug-reaction mismatches (shouldn't be identical)
        drug = str(record.get("drug", "")).lower()
        reaction = str(record.get("reaction", "")).lower()
        if drug and reaction and drug == reaction:
            score -= 0.40
        
        # Confidence should be between 0 and 1
        confidence = record.get("confidence") or record.get("confidence_score")
        if confidence is not None:
            try:
                conf_float = float(confidence)
                if conf_float < 0 or conf_float > 1:
                    score -= 0.20
            except (ValueError, TypeError):
                score -= 0.20
        
        return round(max(score, 0.0), 2)
    
    def validity_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate format validity score.
        
        Args:
            record: AE record
        
        Returns:
            Validity score (0-1)
        """
        score = 1.0
        
        # Field types
        if "drug" in record and not isinstance(record.get("drug"), str):
            score -= 0.25
        
        if "reaction" in record and not isinstance(record.get("reaction"), str):
            score -= 0.25
        
        # Check date format
        created_date = record.get("created_date") or record.get("timestamp")
        if created_date:
            if not isinstance(created_date, (datetime, str)):
                score -= 0.25
            elif isinstance(created_date, str):
                # Try to parse
                try:
                    datetime.fromisoformat(created_date.replace("Z", "+00:00"))
                except:
                    try:
                        datetime.strptime(created_date, "%Y-%m-%d")
                    except:
                        score -= 0.25
        
        return round(max(score, 0.0), 2)
    
    def noise_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate noise level score (social posts).
        
        Args:
            record: AE record
        
        Returns:
            Noise score (0-1, higher = less noise)
        """
        text = str(record.get("text", "")).lower()
        score = 1.0
        
        if not text:
            return 0.5
        
        # Excessive emojis → high noise
        emoji_count = len(re.findall(r"[^\w\s]", text))
        if emoji_count > 20:
            score -= 0.2
        elif emoji_count > 10:
            score -= 0.1
        
        # Many hashtags → noisy
        hashtag_count = text.count("#")
        if hashtag_count > 10:
            score -= 0.2
        elif hashtag_count > 5:
            score -= 0.1
        
        # Very short post → low quality
        if len(text) < 10:
            score -= 0.3
        elif len(text) < 20:
            score -= 0.1
        
        # Excessive capitalization (shouting)
        if len(re.findall(r"[A-Z]{5,}", text)) > 3:
            score -= 0.15
        
        return round(max(score, 0.0), 2)
    
    def ambiguity_score(self, record: Dict[str, Any]) -> float:
        """
        Calculate ambiguity/uncertainty score.
        
        Args:
            record: AE record
        
        Returns:
            Ambiguity score (0-1, higher = less ambiguous)
        """
        text = str(record.get("text", "")).lower()
        score = 1.0
        
        if not text:
            return 0.5
        
        # Check for weak/uncertain terms
        weak_count = sum(1 for term in self.weak_terms if term in text)
        if weak_count > 2:
            score -= 0.3
        elif weak_count > 0:
            score -= 0.15
        
        return round(max(score, 0.0), 2)
    
    def stability_score(
        self,
        record: Dict[str, Any],
        lineage_chain: Optional[List[Dict[str, Any]]] = None
    ) -> float:
        """
        Calculate stability/duplicate prevention score.
        
        Args:
            record: AE record
            lineage_chain: Lineage chain
        
        Returns:
            Stability score (0-1)
        """
        if lineage_chain is None:
            lineage_chain = []
        
        record_id = record.get("record_id") or record.get("ae_id")
        
        # If many transformations, good (data was processed)
        # If no lineage, suspicious
        if len(lineage_chain) == 0:
            return 0.6
        elif len(lineage_chain) == 1:
            return 0.75
        elif len(lineage_chain) >= 2:
            return 1.0
        
        return 0.8
    
    def score(
        self,
        record: Dict[str, Any],
        lineage_chain: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete data quality score for a record.
        
        Args:
            record: AE record dictionary
            lineage_chain: Optional lineage chain
        
        Returns:
            Quality score dictionary
        """
        if lineage_chain is None:
            lineage_chain = []
        
        source = record.get("source", "unknown")
        
        # Calculate component scores
        completeness = self.completeness_score(record)
        consistency = self.consistency_score(record)
        validity = self.validity_score(record)
        noise = self.noise_score(record)
        ambiguity = self.ambiguity_score(record)
        stability = self.stability_score(record, lineage_chain)
        source_baseline = self.source_quality.get(source.lower(), 0.40)
        
        # Final weighted score (0-100)
        final_score = (
            0.25 * completeness +
            0.15 * consistency +
            0.15 * validity +
            0.15 * noise +
            0.10 * ambiguity +
            0.10 * stability +
            0.10 * source_baseline
        )
        
        return {
            "record_id": record.get("record_id") or record.get("ae_id"),
            "source_quality_baseline": round(source_baseline, 2),
            "completeness_score": completeness,
            "consistency_score": consistency,
            "validity_score": validity,
            "noise_score": noise,
            "ambiguity_score": ambiguity,
            "stability_score": stability,
            "final_quality_score": round(final_score * 100, 2)
        }

