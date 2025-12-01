"""
Metriport Client (Paid Source).
EHR/claims data integration from hospitals and health systems.
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class MetriportClient(SourceClientBase):
    """
    Client for Metriport - EHR/claims data integration.
    Paid service - requires API key.
    """
    
    BASE_URL = "https://api.metriport.com/medical/v1/adverse-events"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("METRIPORT_API_KEY", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from Metriport.
        
        Args:
            query: Query parameters
                - drug_name: Drug name
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
            "x-api-key": self.api_key,
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
        for item in data.get("adverseEvents", [])[:limit]:
            normalized = self.normalize_entry({
                "timestamp": item.get("date") or item.get("eventDate"),
                "drug": drug_name,
                "reaction": item.get("reaction") or item.get("adverseEvent"),
                "text": item.get("description", "") or item.get("notes", ""),
                "metadata": item
            })
            results.append(normalized)
        
        return results

