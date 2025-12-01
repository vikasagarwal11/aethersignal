"""
ClinicalTrials.gov API Client.
Fetches adverse event data from ClinicalTrials.gov.
"""

import requests
from typing import Dict, Any, List
from datetime import datetime

from ..base import SourceClientBase


class ClinicalTrialsClient(SourceClientBase):
    """
    Client for ClinicalTrials.gov API.
    Free, no authentication required.
    """
    
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events from ClinicalTrials.gov.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to search
                - reaction: Reaction term (optional)
                - limit: Number of results (default: 50)
        
        Returns:
            List of normalized AE entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        limit = query.get("limit", 50)
        reaction = query.get("reaction")
        
        # Build search query
        search_query = f"{drug_name} adverse event"
        if reaction:
            search_query += f" {reaction}"
        
        # ClinicalTrials.gov API parameters
        params = {
            "query.cond": drug_name,
            "filter.overallStatus": "COMPLETED",
            "pageSize": min(limit, 100),
            "pageToken": ""
        }
        
        # Make request
        response = requests.get(self.BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Normalize results
        results = []
        for study in data.get("studies", [])[:limit]:
            normalized = self._normalize_clinicaltrials_entry(study, drug_name, reaction)
            if normalized:
                results.append(normalized)
        
        return results
    
    def _normalize_clinicaltrials_entry(
        self,
        study: Dict[str, Any],
        drug_name: str,
        reaction: str = None
    ) -> Dict[str, Any]:
        """
        Normalize ClinicalTrials.gov entry to unified format.
        
        Args:
            study: Raw study entry
            drug_name: Drug name
            reaction: Reaction term (optional)
        
        Returns:
            Normalized entry
        """
        # Extract adverse events from study
        protocol_section = study.get("protocolSection", {})
        results_section = study.get("resultsSection", {})
        
        # Get adverse events
        adverse_events = []
        if results_section:
            ae_module = results_section.get("adverseEventsModule", {})
            events = ae_module.get("events", [])
            for event in events:
                term = event.get("title")
                if term:
                    adverse_events.append(term)
        
        # If no specific reaction found, use first adverse event or None
        detected_reaction = reaction or (adverse_events[0] if adverse_events else None)
        
        # Extract dates
        dates = protocol_section.get("statusModule", {}).get("studyFirstPostDateStruct", {})
        timestamp = dates.get("date") if dates else None
        
        # Extract description
        description = protocol_section.get("descriptionModule", {}).get("briefSummary", "")
        
        return {
            "timestamp": timestamp,
            "drug": drug_name,
            "reaction": detected_reaction,
            "reactions": adverse_events,
            "confidence": 0.8,  # Clinical trials are reliable
            "severity": 0.0,  # Can't determine from summary
            "text": description[:500] if description else f"Clinical trial for {drug_name}",
            "source": "clinicaltrials",
            "metadata": {
                "nct_id": study.get("nctId"),
                "study_type": protocol_section.get("designModule", {}).get("studyType"),
                "phase": protocol_section.get("designModule", {}).get("phases", [None])[0],
                "adverse_events_count": len(adverse_events)
            }
        }

