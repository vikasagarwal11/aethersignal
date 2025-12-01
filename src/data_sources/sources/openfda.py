"""
OpenFDA API Client.
Fetches adverse event data from FDA's OpenFDA API.
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..base import SourceClientBase


class OpenFDAClient(SourceClientBase):
    """
    Client for OpenFDA Drug Event API.
    Free, no authentication required (but API key optional for higher rate limits).
    """
    
    BASE_URL = "https://api.fda.gov/drug/event.json"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("OPENFDA_API_KEY")
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from OpenFDA.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to search
                - reaction: Reaction term (optional)
                - limit: Number of results (default: 100)
                - date_range: Tuple of (start_date, end_date) (optional)
        
        Returns:
            List of normalized AE entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        limit = query.get("limit", 100)
        reaction = query.get("reaction")
        
        # Build search query
        search_terms = [f'patient.drug.medicinalproduct:"{drug_name}"']
        if reaction:
            search_terms.append(f'patient.reaction.reactionmeddrapt:"{reaction}"')
        
        search_query = "+AND+".join(search_terms)
        
        # Build URL
        params = {
            "search": search_query,
            "limit": min(limit, 100),  # OpenFDA max is 100
            "skip": 0
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        # Make request
        response = requests.get(self.BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Normalize results
        results = []
        for result in data.get("results", []):
            normalized = self._normalize_openfda_entry(result, drug_name)
            if normalized:
                results.append(normalized)
        
        return results
    
    def _normalize_openfda_entry(self, entry: Dict[str, Any], drug_name: str) -> Dict[str, Any]:
        """
        Normalize OpenFDA entry to unified format.
        
        Args:
            entry: Raw OpenFDA entry
            drug_name: Drug name from query
        
        Returns:
            Normalized entry
        """
        # Extract reaction
        reactions = []
        for reaction in entry.get("patient", {}).get("reaction", []):
            reaction_pt = reaction.get("reactionmeddrapt")
            if reaction_pt:
                reactions.append(reaction_pt)
        
        # Extract date
        received_date = entry.get("receivedate")
        if received_date:
            try:
                # OpenFDA dates are in YYYYMMDD format
                date_obj = datetime.strptime(received_date, "%Y%m%d")
                timestamp = date_obj.isoformat()
            except:
                timestamp = received_date
        else:
            timestamp = None
        
        # Extract narrative/summary
        narrative = entry.get("summary", {}).get("narrative", "")
        
        return {
            "timestamp": timestamp,
            "drug": drug_name,
            "reaction": reactions[0] if reactions else None,
            "reactions": reactions,  # Multiple reactions
            "confidence": 1.0,  # OpenFDA is authoritative
            "severity": self._estimate_severity(entry),
            "text": narrative or f"Adverse event report for {drug_name}",
            "source": "openfda",
            "metadata": {
                "report_id": entry.get("safetyreportid"),
                "serious": entry.get("serious"),
                "outcome": entry.get("patient", {}).get("reaction", [{}])[0].get("reactionoutcome"),
                "raw_entry": entry
            }
        }
    
    def _estimate_severity(self, entry: Dict[str, Any]) -> float:
        """Estimate severity from OpenFDA entry."""
        severity = 0.0
        
        # Check serious flag
        if entry.get("serious") == 1:
            severity += 0.5
        
        # Check outcomes
        outcomes = []
        for reaction in entry.get("patient", {}).get("reaction", []):
            outcome = reaction.get("reactionoutcome")
            if outcome:
                outcomes.append(outcome.lower())
        
        if any("death" in o or "fatal" in o for o in outcomes):
            severity += 0.5
        elif any("hospital" in o or "life" in o for o in outcomes):
            severity += 0.3
        elif any("disability" in o for o in outcomes):
            severity += 0.2
        
        return min(1.0, severity)

