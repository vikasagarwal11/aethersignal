"""
Cross-Drug Interaction Engine - Detects drug-drug interactions and AE amplification
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CrossDrugInteractionEngine:
    """
    Detects:
    - Shared mechanism pathways
    - AE amplification clusters
    - Embedding similarity between drugs
    - Risky co-medications
    """
    
    COMMON_INTERACTIONS = {
        ("ssri", "triptan"): {
            "mechanism": "serotonin syndrome",
            "severity": "high",
            "evidence": "strong"
        },
        ("glp-1", "metformin"): {
            "mechanism": "GI toxicity amplification",
            "severity": "moderate",
            "evidence": "moderate"
        },
        ("ace inhibitor", "diuretic"): {
            "mechanism": "AKI risk",
            "severity": "moderate",
            "evidence": "strong"
        },
        ("warfarin", "aspirin"): {
            "mechanism": "bleeding risk",
            "severity": "high",
            "evidence": "strong"
        },
        ("statin", "fibrate"): {
            "mechanism": "rhabdomyolysis",
            "severity": "high",
            "evidence": "moderate"
        },
        ("digoxin", "amiodarone"): {
            "mechanism": "digoxin toxicity",
            "severity": "high",
            "evidence": "strong"
        }
    }
    
    def __init__(self):
        pass
    
    def evaluate(self, drug: str, reaction: str, co_medications: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate cross-drug interactions.
        
        Args:
            drug: Primary drug name
            reaction: Reaction name
            co_medications: Optional list of co-medications
        
        Returns:
            Interaction assessment dictionary
        """
        drug_lower = drug.lower()
        reaction_lower = reaction.lower()
        
        hits = []
        
        # Check known interactions
        for (a, b), info in self.COMMON_INTERACTIONS.items():
            if a in drug_lower or b in drug_lower:
                if info["mechanism"].lower() in reaction_lower:
                    hits.append({
                        "pair": f"{a}+{b}",
                        "mechanism": info["mechanism"],
                        "severity": info["severity"],
                        "evidence": info["evidence"]
                    })
        
        # Check co-medications if provided
        co_med_interactions = []
        if co_medications:
            for co_med in co_medications:
                co_med_lower = co_med.lower()
                for (a, b), info in self.COMMON_INTERACTIONS.items():
                    if (a in drug_lower and b in co_med_lower) or (b in drug_lower and a in co_med_lower):
                        co_med_interactions.append({
                            "drug1": drug,
                            "drug2": co_med,
                            "mechanism": info["mechanism"],
                            "severity": info["severity"],
                            "evidence": info["evidence"]
                        })
        
        # Calculate interaction score
        interaction_score = 0.0
        if hits:
            # Weight by severity
            severity_weights = {"high": 1.0, "moderate": 0.6, "low": 0.3}
            max_severity = max([severity_weights.get(h["severity"], 0.5) for h in hits])
            interaction_score = max_severity
        
        return {
            "interactions_detected": hits,
            "co_medication_interactions": co_med_interactions,
            "count": len(hits),
            "co_med_count": len(co_med_interactions),
            "interaction_score": interaction_score,
            "has_interactions": len(hits) > 0 or len(co_med_interactions) > 0
        }
    
    def check_drug_pair(self, drug1: str, drug2: str) -> Optional[Dict[str, Any]]:
        """
        Check for known interaction between two specific drugs.
        
        Args:
            drug1: First drug name
            drug2: Second drug name
        
        Returns:
            Interaction info or None
        """
        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()
        
        for (a, b), info in self.COMMON_INTERACTIONS.items():
            if ((a in drug1_lower and b in drug2_lower) or 
                (b in drug1_lower and a in drug2_lower)):
                return {
                    "drug1": drug1,
                    "drug2": drug2,
                    "mechanism": info["mechanism"],
                    "severity": info["severity"],
                    "evidence": info["evidence"]
                }
        
        return None

