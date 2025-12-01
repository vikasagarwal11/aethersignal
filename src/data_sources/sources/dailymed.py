"""
DailyMed API Client.
Fetches adverse event information from DailyMed drug labels.
"""

import requests
from typing import Dict, Any, List
from datetime import datetime
import re

from ..base import SourceClientBase


class DailyMedClient(SourceClientBase):
    """
    Client for DailyMed API.
    Free, no authentication required.
    Provides drug label information including adverse reactions.
    """
    
    BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse event information from DailyMed labels.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to search
                - reaction: Reaction term (optional, for filtering)
                - limit: Number of results (default: 20)
        
        Returns:
            List of normalized AE entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        limit = query.get("limit", 20)
        reaction = query.get("reaction")
        
        # Search for drug labels
        search_url = f"{self.BASE_URL}/drugnames.json"
        search_params = {
            "drug_name": drug_name
        }
        
        response = requests.get(search_url, params=search_params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Get first matching drug
        drugs = data.get("data", [])
        if not drugs:
            return []
        
        # Get label for first drug
        drug_set_id = drugs[0].get("spl_set_id")
        if not drug_set_id:
            return []
        
        # Fetch label
        label_url = f"{self.BASE_URL}/spls/{drug_set_id}.json"
        label_response = requests.get(label_url, timeout=30)
        label_response.raise_for_status()
        label_data = label_response.json()
        
        # Extract adverse reactions section
        results = self._extract_adverse_reactions(label_data, drug_name, reaction)
        
        return results[:limit]
    
    def _extract_adverse_reactions(
        self,
        label_data: Dict[str, Any],
        drug_name: str,
        reaction_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Extract adverse reactions from DailyMed label.
        
        Args:
            label_data: Label JSON data
            drug_name: Drug name
            reaction_filter: Optional reaction to filter for
        
        Returns:
            List of normalized entries
        """
        results = []
        
        # Extract adverse reactions section
        # DailyMed structure varies, so we search for common patterns
        label_text = str(label_data)
        
        # Look for adverse reactions section
        # This is simplified - full implementation would parse XML/structured data properly
        adverse_section_patterns = [
            r"ADVERSE REACTIONS[:\s]+(.*?)(?=WARNINGS|PRECAUTIONS|DOSAGE|$)",
            r"Side Effects[:\s]+(.*?)(?=Warnings|Precautions|Dosage|$)",
        ]
        
        adverse_text = ""
        for pattern in adverse_section_patterns:
            match = re.search(pattern, label_text, re.IGNORECASE | re.DOTALL)
            if match:
                adverse_text = match.group(1)
                break
        
        if not adverse_text:
            return []
        
        # Extract individual reactions (simplified)
        # Common reaction patterns
        reaction_patterns = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:,|;|\.|and)",
        ]
        
        reactions_found = []
        for pattern in reaction_patterns:
            matches = re.findall(pattern, adverse_text)
            reactions_found.extend(matches)
        
        # Filter if specific reaction requested
        if reaction_filter:
            reactions_found = [
                r for r in reactions_found
                if reaction_filter.lower() in r.lower()
            ]
        
        # Create entries for each reaction
        for reaction in reactions_found[:20]:  # Limit to 20
            results.append({
                "timestamp": datetime.now().isoformat(),  # Label date not always available
                "drug": drug_name,
                "reaction": reaction.strip(),
                "confidence": 0.9,  # Label information is authoritative
                "severity": 0.0,  # Labels don't specify severity
                "text": f"Adverse reaction '{reaction}' listed in {drug_name} label",
                "source": "dailymed",
                "metadata": {
                    "type": "label",
                    "source_section": "adverse_reactions"
                }
            })
        
        return results

