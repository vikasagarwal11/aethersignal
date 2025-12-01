"""
Cerner FHIR Client (Paid Source).
Hospital EHR integration via Cerner FHIR API.
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class CernerFHIRClient(SourceClientBase):
    """
    Client for Cerner FHIR - Hospital EHR integration.
    Paid service - requires API key and Cerner partnership.
    """
    
    BASE_URL = "https://fhir.cerner.com/r4"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("CERNER_FHIR_KEY", "")
        self.client_id = os.getenv("CERNER_FHIR_CLIENT_ID", "")
        self.client_secret = os.getenv("CERNER_FHIR_CLIENT_SECRET", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from Cerner FHIR.
        
        Args:
            query: Query parameters
                - drug_name: Drug name
                - patient_id: Optional patient ID
                - limit: Number of results
        
        Returns:
            List of normalized AE entries (or dummy data if in dummy mode)
        """
        if not self.api_key and not self.client_id:
            # Return dummy data if in dummy mode, empty otherwise
            if self.fallback_mode == "dummy":
                return self.fallback()
            return []  # Silent fallback - no key
        
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        # Cerner FHIR requires OAuth2 token first
        try:
            token = self._get_access_token()
            if not token:
                return self.fallback() if self.fallback_mode == "dummy" else []
        except Exception:
            return self.fallback() if self.fallback_mode == "dummy" else []
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/fhir+json"
        }
        
        # Search for AdverseEvent resources
        search_url = f"{self.BASE_URL}/AdverseEvent"
        params = {
            "code": drug_name,
            "_count": min(query.get("limit", 50), 100)
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return self.fallback() if self.fallback_mode == "dummy" else []
        
        results = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            normalized = self.normalize_entry({
                "timestamp": resource.get("date"),
                "drug": drug_name,
                "reaction": resource.get("event", {}).get("text"),
                "text": resource.get("description", {}).get("text", ""),
                "metadata": resource
            })
            results.append(normalized)
        
        return results
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token from Cerner."""
        if not self.client_id or not self.client_secret:
            return ""
        
        token_url = "https://authorization.cerner.com/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token", "")

