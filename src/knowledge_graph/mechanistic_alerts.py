"""
Mechanistic Alerts - Real-time alerts based on mechanism scores
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MechanisticAlerts:
    """
    Alerts are triggered when:
    - High fusion score (embedding)
    - High causal strength
    - High novelty
    - Strong mechanistic explanation
    """
    
    def __init__(self, threshold: float = 0.80):
        """
        Initialize alert engine.
        
        Args:
            threshold: Alert threshold (0-1)
        """
        self.threshold = threshold
    
    def evaluate(
        self,
        scores: Dict[str, float],
        is_novel: bool,
        causal: Dict[str, float],
        drug: str = None,
        reaction: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate if an alert should be triggered.
        
        Args:
            scores: Fusion scores dictionary
            is_novel: Whether signal is novel
            causal: Causal inference scores
            drug: Drug name (optional)
            reaction: Reaction name (optional)
        
        Returns:
            Alert evaluation dictionary
        """
        fusion = scores.get("fusion_score", 0.0)
        causal_score = causal.get("causal_score", 0.0)
        
        # Calculate alert score
        alert_score = (
            0.5 * fusion +
            0.3 * causal_score +
            (0.2 if is_novel else 0.0)
        )
        
        # Ensure alert_score is in [0, 1]
        alert_score = max(0.0, min(1.0, alert_score))
        
        return {
            "alert": alert_score >= self.threshold,
            "alert_score": float(alert_score),
            "fusion": float(fusion),
            "causal": float(causal_score),
            "is_novel": is_novel,
            "drug": drug,
            "reaction": reaction,
            "threshold": self.threshold
        }
    
    def batch_evaluate(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate multiple drug-reaction pairs.
        
        Args:
            evaluations: List of evaluation dictionaries
        
        Returns:
            List of alert evaluations
        """
        results = []
        for eval_data in evaluations:
            result = self.evaluate(
                scores=eval_data.get("scores", {}),
                is_novel=eval_data.get("is_novel", False),
                causal=eval_data.get("causal", {}),
                drug=eval_data.get("drug"),
                reaction=eval_data.get("reaction")
            )
            results.append(result)
        
        # Sort by alert score (highest first)
        results.sort(key=lambda x: x["alert_score"], reverse=True)
        
        return results
    
    def get_high_priority_alerts(self, evaluations: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get top K high-priority alerts.
        
        Args:
            evaluations: List of evaluation dictionaries
            top_k: Number of top alerts to return
        
        Returns:
            List of high-priority alerts
        """
        all_results = self.batch_evaluate(evaluations)
        
        # Filter to only alerts that triggered
        triggered = [r for r in all_results if r["alert"]]
        
        return triggered[:top_k]

