"""
Bradford-Hill Causality Matrix Engine
Evaluates 9 Bradford-Hill criteria for causality assessment
"""

import logging
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class BradfordHillEngine:
    """Evaluates Bradford-Hill criteria for causality assessment."""
    
    CRITERIA = [
        "strength",
        "consistency",
        "specificity",
        "temporality",
        "biological_gradient",
        "plausibility",
        "coherence",
        "experiment",
        "analogy"
    ]
    
    def score(
        self,
        drug: str,
        ae: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score Bradford-Hill criteria.
        
        Args:
            drug: Drug name
            ae: Adverse event
            evidence: Evidence dictionary with scores for each criterion
        
        Returns:
            Dictionary with criteria scores and overall assessment
        """
        scores = {}
        
        # Extract scores from evidence (0.0 to 1.0 scale)
        for criterion in self.CRITERIA:
            key = f"{criterion}_score"
            scores[criterion] = evidence.get(key, 0.0)
        
        # Calculate weighted overall score
        # Temporality and dose-response are most important
        weights = {
            "strength": 0.10,
            "consistency": 0.10,
            "specificity": 0.05,
            "temporality": 0.20,  # Most important
            "biological_gradient": 0.15,  # Dose-response
            "plausibility": 0.15,
            "coherence": 0.10,
            "experiment": 0.10,
            "analogy": 0.05
        }
        
        weighted_sum = sum(scores[criterion] * weights.get(criterion, 0.1) for criterion in self.CRITERIA)
        overall = round(weighted_sum, 3)
        
        # Determine causality level
        if overall >= 0.7:
            causality_level = "HIGH"
        elif overall >= 0.5:
            causality_level = "MODERATE"
        elif overall >= 0.3:
            causality_level = "LOW"
        else:
            causality_level = "VERY_LOW"
        
        return {
            "drug": drug,
            "ae": ae,
            "criteria_scores": scores,
            "overall": overall,
            "causality_level": causality_level,
            "weights": weights,
            "meets_criteria": {
                criterion: scores[criterion] >= 0.5
                for criterion in self.CRITERIA
            }
        }
    
    def evaluate_temporality(
        self,
        onset_times: list,
        drug_start_times: list
    ) -> float:
        """
        Evaluate temporality criterion (onset after drug exposure).
        
        Args:
            onset_times: List of AE onset times
            drug_start_times: List of drug start times
        
        Returns:
            Temporality score (0.0 to 1.0)
        """
        if not onset_times or not drug_start_times:
            return 0.0
        
        # Count how many AEs occurred after drug start
        valid_pairs = 0
        temporal_pairs = 0
        
        for onset, drug_start in zip(onset_times, drug_start_times):
            if onset and drug_start:
                valid_pairs += 1
                if onset >= drug_start:
                    temporal_pairs += 1
        
        if valid_pairs == 0:
            return 0.0
        
        return temporal_pairs / valid_pairs
    
    def evaluate_dose_response(
        self,
        dose_data: Dict[float, int]
    ) -> float:
        """
        Evaluate biological gradient (dose-response) criterion.
        
        Args:
            dose_data: Dictionary mapping doses to AE counts
        
        Returns:
            Dose-response score (0.0 to 1.0)
        """
        if not dose_data or len(dose_data) < 2:
            return 0.0
        
        # Check if higher doses correlate with more AEs
        sorted_doses = sorted(dose_data.keys())
        counts = [dose_data[dose] for dose in sorted_doses]
        
        # Calculate correlation
        if len(counts) >= 2:
            correlation = np.corrcoef(range(len(counts)), counts)[0, 1]
            # Convert correlation (-1 to 1) to score (0 to 1)
            return max(0.0, correlation)
        
        return 0.0

