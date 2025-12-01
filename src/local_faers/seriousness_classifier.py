"""
Seriousness Classifier (CHUNK 7.8 Part 3)
Local classification of case seriousness based on structured and text fields.
"""
from typing import Dict, List, Any, Optional


class SeriousnessClassifier:
    """
    Classifies case seriousness from FAERS data.
    
    Maps structured seriousness fields and outcome codes to binary serious/non-serious.
    """
    
    # Serious outcome codes (FDA/ICH standard)
    SERIOUS_OUTCOME_CODES = {
        "DE": "Death",
        "LT": "Life-Threatening",
        "HO": "Hospitalization",
        "DS": "Disability",
        "CA": "Congenital Anomaly",
        "RI": "Required Intervention",
        "OT": "Other Serious"
    }
    
    # Seriousness field mappings
    SERIOUSNESS_FIELDS = [
        "seriousness_death",
        "seriousness_life_threatening",
        "seriousness_hospitalization",
        "seriousness_disabling",
        "seriousness_congenital_anomali",
        "seriousness_other",
        "seriousness_other_medically_important",
    ]
    
    def classify(self, case_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify case seriousness.
        
        Args:
            case_record: Case record with outcome codes and seriousness fields
            
        Returns:
            Dictionary with seriousness classification
        """
        serious = False
        seriousness_reasons = []
        
        # Check outcome codes
        outcomes = case_record.get("outcomes", [])
        if not outcomes and case_record.get("outcome"):
            outcomes = [case_record.get("outcome")]
        
        for outcome_code in outcomes:
            outcome_str = str(outcome_code).strip().upper()
            if outcome_str in self.SERIOUS_OUTCOME_CODES:
                serious = True
                seriousness_reasons.append(self.SERIOUS_OUTCOME_CODES[outcome_str])
        
        # Check structured seriousness fields
        for field in self.SERIOUSNESS_FIELDS:
            field_variations = [
                field,
                field.upper(),
                field.lower(),
                field.replace("_", ""),
                field.replace("_", " ").title()
            ]
            
            for var in field_variations:
                value = case_record.get(var)
                if value in ["1", "Y", "YES", "TRUE", True, 1]:
                    serious = True
                    seriousness_reasons.append(field.replace("_", " ").title())
                    break
        
        # Check for serious keywords in text fields
        text_fields = ["narrative", "description", "event_description"]
        for field in text_fields:
            text = case_record.get(field, "")
            if text and isinstance(text, str):
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ["death", "died", "fatal", "life threatening", "hospitalized"]):
                    serious = True
                    seriousness_reasons.append("Text keyword match")
                    break
        
        return {
            "serious": serious,
            "seriousness_reasons": list(set(seriousness_reasons)),  # Deduplicate
            "seriousness_level": "serious" if serious else "non-serious"
        }
    
    def classify_batch(self, case_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple case records.
        
        Args:
            case_records: List of case records
            
        Returns:
            List of case records with seriousness classification added
        """
        classified = []
        for record in case_records:
            classification = self.classify(record)
            record.update(classification)
            classified.append(record)
        
        return classified

