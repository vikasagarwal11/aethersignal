"""
OHDSI Client (Paid Source).
Observational Health Data Sciences and Informatics - Research-grade EHR data.
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class OHDSIClient(SourceClientBase):
    """
    Client for OHDSI - Observational Health Data Sciences and Informatics.
    Paid service - requires API key and subscription.
    """
    
    BASE_URL = "https://api.ohdsi.org/WebAPI/evidence"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("OHDSI_KEY", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from OHDSI.
        
        Args:
            query: Query parameters
                - drug_name: Drug name
                - reaction: Reaction term (optional)
                - limit: Number of results
        
        Returns:
            List of normalized AE entries
        """
        if not self.api_key:
            return []  # Silent fallback - no key
        
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        limit = query.get("limit", 50)
        reaction = query.get("reaction")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OHDSI evidence API
        params = {
            "drug": drug_name,
            "limit": min(limit, 100)
        }
        
        if reaction:
            params["outcome"] = reaction
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []  # Silent fallback on error
        
        results = []
        for item in data.get("evidence", [])[:limit]:
            normalized = self.normalize_entry({
                "timestamp": item.get("date") or item.get("studyDate"),
                "drug": drug_name,
                "reaction": item.get("outcome") or item.get("adverseEvent"),
                "text": item.get("description", "") or f"OHDSI evidence for {drug_name}",
                "metadata": {
                    "study_id": item.get("studyId"),
                    "cohort_id": item.get("cohortId"),
                    "evidence_type": item.get("evidenceType"),
                    **item
                }
            })
            results.append(normalized)
        
        return results

