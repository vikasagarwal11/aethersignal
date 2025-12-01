"""
Quality Scorer - Phase 3L Step 4
Calculates data quality scores (0-1) based on completeness, reliability, recency, consistency.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .config import QUALITY_WEIGHTS, get_evidence_class_weight, get_quality_threshold

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Calculates quality scores for AE records.
    """
    
    def __init__(self):
        """Initialize quality scorer."""
        self.weights = QUALITY_WEIGHTS
    
    def score_record(
        self,
        record: Dict[str, Any],
        source: str,
        comparison_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate quality score for a single record.
        
        Args:
            record: AE record dictionary
            source: Source name
            comparison_records: Optional list of similar records for consistency check
        
        Returns:
            Dictionary with quality score and components
        """
        components = {}
        
        # 1. Completeness (25%)
        completeness = self._calculate_completeness(record)
        components["completeness"] = completeness
        
        # 2. Source Reliability (25%)
        source_reliability = get_evidence_class_weight(source)
        components["source_reliability"] = source_reliability
        
        # 3. Recency (20%)
        recency = self._calculate_recency(record)
        components["recency"] = recency
        
        # 4. Consistency (20%)
        consistency = self._calculate_consistency(record, comparison_records)
        components["consistency"] = consistency
        
        # 5. Duplicate Penalty (-10%)
        duplicate_penalty = self._calculate_duplicate_penalty(record, comparison_records)
        components["duplicate_penalty"] = duplicate_penalty
        
        # Calculate weighted score
        quality_score = (
            completeness * self.weights["completeness"] +
            source_reliability * self.weights["source_reliability"] +
            recency * self.weights["recency"] +
            consistency * self.weights["consistency"] +
            duplicate_penalty * abs(self.weights["duplicate_penalty"])
        )
        
        # Ensure score is between 0 and 1
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Get threshold category
        threshold = get_quality_threshold(quality_score)
        
        return {
            "quality_score": round(quality_score, 3),
            "threshold": threshold,
            "components": components
        }
    
    def _calculate_completeness(self, record: Dict[str, Any]) -> float:
        """Calculate completeness score (0-1)."""
        required_fields = ["drug", "reaction", "source", "created_date"]
        optional_fields = ["severity_score", "quantum_score", "confidence", "country", "text"]
        
        required_count = sum(1 for field in required_fields if record.get(field) not in [None, "", "unknown"])
        optional_count = sum(1 for field in optional_fields if record.get(field) not in [None, "", "unknown"])
        
        required_score = required_count / len(required_fields) if required_fields else 1.0
        optional_score = optional_count / len(optional_fields) if optional_fields else 0.0
        
        # Weighted: 70% required, 30% optional
        completeness = (required_score * 0.7) + (optional_score * 0.3)
        
        return completeness
    
    def _calculate_recency(self, record: Dict[str, Any]) -> float:
        """Calculate recency score (0-1)."""
        if "created_date" not in record:
            return 0.5  # Default moderate
        
        try:
            record_date = pd.to_datetime(record["created_date"], errors="coerce")
            if pd.isna(record_date):
                return 0.5
            
            days_old = (datetime.now() - record_date.to_pydatetime()).days
            
            # Score: 1.0 for today, 0.8 for 7 days, 0.5 for 30 days, 0.2 for 90 days
            if days_old <= 1:
                return 1.0
            elif days_old <= 7:
                return 0.9
            elif days_old <= 30:
                return 0.7
            elif days_old <= 90:
                return 0.5
            elif days_old <= 180:
                return 0.3
            else:
                return 0.1
        except Exception:
            return 0.5
    
    def _calculate_consistency(
        self,
        record: Dict[str, Any],
        comparison_records: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate consistency score (0-1)."""
        if not comparison_records:
            return 0.7  # Default moderate if no comparison
        
        # Check if reaction appears in similar records
        reaction = record.get("reaction", "")
        if not reaction:
            return 0.5
        
        matching_count = sum(
            1 for r in comparison_records
            if r.get("reaction", "").lower() == reaction.lower()
        )
        
        consistency = min(1.0, matching_count / max(1, len(comparison_records)) * 2)
        
        return consistency
    
    def _calculate_duplicate_penalty(
        self,
        record: Dict[str, Any],
        comparison_records: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate duplicate penalty (negative value)."""
        if not comparison_records:
            return 0.0
        
        # Check for exact duplicates
        record_fingerprint = str(sorted(record.items()))
        duplicate_count = sum(
            1 for r in comparison_records
            if str(sorted(r.items())) == record_fingerprint
        )
        
        # Penalty increases with duplicates
        penalty = -0.1 * min(duplicate_count, 5)  # Max -0.5 penalty
        
        return penalty
    
    def score_dataframe(
        self,
        df: pd.DataFrame,
        source_col: str = "source"
    ) -> pd.DataFrame:
        """
        Score all records in a DataFrame.
        
        Args:
            df: DataFrame with AE records
            source_col: Column name for source
        
        Returns:
            DataFrame with quality_score column added
        """
        if df.empty:
            return df
        
        scores = []
        for idx, row in df.iterrows():
            record = row.to_dict()
            source = record.get(source_col, "unknown")
            
            # Get comparison records (other records with same drug-reaction)
            if "drug" in df.columns and "reaction" in df.columns:
                drug = record.get("drug", "")
                reaction = record.get("reaction", "")
                comparison = df[
                    (df["drug"] == drug) &
                    (df["reaction"] == reaction) &
                    (df.index != idx)
                ]
                comparison_records = comparison.to_dict("records")
            else:
                comparison_records = None
            
            score_result = self.score_record(record, source, comparison_records)
            scores.append(score_result["quality_score"])
        
        df["quality_score"] = scores
        
        return df

