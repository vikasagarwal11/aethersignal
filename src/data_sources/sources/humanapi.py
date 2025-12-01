"""
Human API Client (Paid Source).
Patient health data aggregation from EHRs, labs, pharmacies.
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class HumanAPIClient(SourceClientBase):
    """
    Client for Human API - Patient health data aggregation.
    Paid service - requires API key.
    """
    
    BASE_URL = "https://api.humanapi.co/v1/medical/events"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("HUMAN_API_KEY", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from Human API.
        
        Args:
            query: Query parameters
                - drug_name: Drug name
                - patient_id: Optional patient ID
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
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "drug": drug_name,
            "limit": min(limit, 100)
        }
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []  # Silent fallback on error
        
        results = []
        for item in data.get("events", [])[:limit]:
            normalized = self.normalize_entry({
                "timestamp": item.get("date") or item.get("timestamp"),
                "drug": drug_name,
                "reaction": item.get("eventType") or item.get("adverseEvent"),
                "text": item.get("note", "") or item.get("description", ""),
                "metadata": item
            })
            results.append(normalized)
        
        return results

