"""
VigiBase Client (Paid Source).
WHO global adverse event database (VigiBase).
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class VigiBaseClient(SourceClientBase):
    """
    Client for VigiBase - WHO global adverse event database.
    Paid service - requires API key and subscription.
    """
    
    BASE_URL = "https://api.vigibase.who-umc.org/v1/reports"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("VIGIBASE_KEY", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from VigiBase.
        
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
        
        params = {
            "drug": drug_name,
            "limit": min(limit, 100)
        }
        
        if reaction:
            params["reaction"] = reaction
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []  # Silent fallback on error
        
        results = []
        for item in data.get("reports", [])[:limit]:
            normalized = self.normalize_entry({
                "timestamp": item.get("date") or item.get("receivedDate"),
                "drug": drug_name,
                "reaction": item.get("reaction") or item.get("adverseEvent"),
                "text": item.get("narrative", "") or item.get("description", ""),
                "metadata": {
                    "report_id": item.get("reportId"),
                    "country": item.get("country"),
                    "serious": item.get("serious"),
                    **item
                }
            })
            results.append(normalized)
        
        return results

