"""
Toxicology Reasoner - Toxicology-based mechanistic reasoning
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ToxicologyReasoner:
    """
    Lightweight toxicology reasoner.
    Uses:
    - Toxicity keywords
    - Chemical class risk
    - Known organ system effects
    - Fallback LLM if available
    """
    
    TOX_KEYWORDS = {
        "hepatotoxicity": ["liver", "hepatitis", "AST", "ALT", "jaundice", "bilirubin"],
        "cardio": ["arrhythmia", "tachycardia", "palpitations", "QT prolongation", "cardiac"],
        "neuro": ["seizure", "tremor", "paresthesia", "neuropathy", "dizziness"],
        "renal": ["nephrotoxicity", "AKI", "creatinine", "kidney", "renal failure"],
        "hematologic": ["thrombocytopenia", "anemia", "neutropenia", "bleeding"],
        "dermatologic": ["rash", "SJS", "TEN", "dermatitis", "urticaria"],
        "gastrointestinal": ["nausea", "vomiting", "diarrhea", "GI bleeding", "pancreatitis"]
    }
    
    CHEMICAL_CLASS_RISK = {
        "GLP-1": ["nausea", "vomiting", "gastroparesis", "pancreatitis"],
        "SSRI": ["serotonin syndrome", "hyponatremia", "bleeding"],
        "ACE inhibitor": ["cough", "angioedema", "AKI"],
        "statin": ["rhabdomyolysis", "myopathy", "hepatotoxicity"],
        "anticoagulant": ["bleeding", "hemorrhage", "thrombocytopenia"]
    }
    
    def __init__(self):
        pass
    
    def evaluate(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Evaluate toxicology match for drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Toxicology assessment dictionary
        """
        reaction_lower = reaction.lower()
        drug_lower = drug.lower()
        
        tox_match = None
        matched_keywords = []
        
        # Keyword scan
        for tox, terms in self.TOX_KEYWORDS.items():
            matches = [t for t in terms if t in reaction_lower]
            if matches:
                tox_match = tox
                matched_keywords = matches
                break
        
        class_match = None
        class_risks = []
        
        # Chemical class risk scan
        for cls, risks in self.CHEMICAL_CLASS_RISK.items():
            if cls.lower() in drug_lower:
                matched_risks = [r for r in risks if r in reaction_lower]
                if matched_risks:
                    class_match = cls
                    class_risks = matched_risks
                    break
        
        # Calculate toxicity score
        tox_score = 0.0
        if tox_match:
            tox_score += 0.6
        if class_match:
            tox_score += 0.4
        
        return {
            "tox_match": tox_match,
            "matched_keywords": matched_keywords,
            "class_match": class_match,
            "class_risks": class_risks,
            "tox_present": tox_match is not None or class_match is not None,
            "tox_score": min(1.0, tox_score)
        }
    
    def get_organ_system(self, reaction: str) -> Optional[str]:
        """
        Determine organ system from reaction.
        
        Args:
            reaction: Reaction name
        
        Returns:
            Organ system or None
        """
        reaction_lower = reaction.lower()
        
        for tox_type, keywords in self.TOX_KEYWORDS.items():
            if any(kw in reaction_lower for kw in keywords):
                return tox_type
        
        return None

