"""
DrugBank Client (Paid Source).
Drug database with chemical structures and drug interactions.
"""

import os
import requests
from typing import Dict, Any, List

from ..base import SourceClientBase


class DrugBankClient(SourceClientBase):
    """
    Client for DrugBank - Drug database and chemical structures.
    Paid service - requires API key.
    """
    
    BASE_URL = "https://api.drugbank.com/v1/drugs"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("DRUGBANK_KEY", "")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse event information from DrugBank.
        
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
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Search for drug
        search_url = f"{self.BASE_URL}/search"
        search_params = {"q": drug_name}
        
        try:
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=20)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            drug_ids = [drug.get("id") for drug in search_data.get("drugs", [])[:5]]
            
            if not drug_ids:
                return []
            
            # Get adverse reactions for first drug
            drug_id = drug_ids[0]
            drug_url = f"{self.BASE_URL}/{drug_id}/adverse-reactions"
            
            drug_response = requests.get(drug_url, headers=headers, timeout=20)
            drug_response.raise_for_status()
            drug_data = drug_response.json()
        except Exception:
            return []  # Silent fallback on error
        
        results = []
        for reaction in drug_data.get("adverseReactions", [])[:20]:
            normalized = self.normalize_entry({
                "timestamp": None,  # DrugBank doesn't provide dates
                "drug": drug_name,
                "reaction": reaction.get("name") or reaction.get("reaction"),
                "text": reaction.get("description", "") or f"Adverse reaction from DrugBank for {drug_name}",
                "metadata": reaction
            })
            results.append(normalized)
        
        return results

