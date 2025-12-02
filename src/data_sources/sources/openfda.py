"""
OpenFDA API Client.
Fetches adverse event data from FDA's OpenFDA API.

OpenFDA provides FREE access to:
- FAERS (Adverse Event Reporting System) - /drug/event
- Drug Labels - /drug/label
- Drug Recalls - /drug/recall

Rate Limits:
- 240 requests/minute (with API key)
- 1 request/second (without key)

No API key required - works without authentication.
"""
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..base import SourceClientBase
from src.utils.config_loader import load_config


class OpenFDAClient(SourceClientBase):
    """
    Client for OpenFDA Drug APIs.
    Free, no authentication required (but API key optional for higher rate limits).
    
    Endpoints:
    - /drug/event - FAERS adverse events
    - /drug/label - Drug labels
    - /drug/recall - Drug recalls
    """
    
    BASE_URL_EVENT = "https://api.fda.gov/drug/event.json"
    BASE_URL_LABEL = "https://api.fda.gov/drug/label.json"
    BASE_URL_RECALL = "https://api.fda.gov/drug/recall.json"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        # Get API key from config file first, then environment
        app_config = load_config()
        self.api_key = (
            app_config.get("api_keys", {}).get("OPENFDA_API_KEY") or
            os.getenv("OPENFDA_API_KEY")
        )
    
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
        response = requests.get(self.BASE_URL_EVENT, params=params, timeout=20)
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
    
    def fetch_labels(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch drug labels from OpenFDA.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to search
                - limit: Number of results (default: 100)
        
        Returns:
            List of drug label entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        if not drug_name:
            return []
        
        limit = query.get("limit", 100)
        
        # Build search query
        search_query = f'openfda.brand_name:"{drug_name}"'
        
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": 0
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL_LABEL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "drug": drug_name,
                    "label": result,
                    "source": "openfda_label",
                    "metadata": {
                        "brand_name": result.get("openfda", {}).get("brand_name", []),
                        "generic_name": result.get("openfda", {}).get("generic_name", []),
                        "product_type": result.get("openfda", {}).get("product_type", []),
                    }
                })
            
            return results
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Error fetching OpenFDA labels: {str(e)}")
            return []
    
    def fetch_recalls(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch drug recalls from OpenFDA.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to search (optional)
                - limit: Number of results (default: 100)
                - date_range: Tuple of (start_date, end_date) (optional)
        
        Returns:
            List of recall entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        limit = query.get("limit", 100)
        
        # Build search query
        search_terms = []
        if drug_name:
            search_terms.append(f'openfda.brand_name:"{drug_name}"')
        
        params = {
            "limit": min(limit, 100),
            "skip": 0
        }
        
        if search_terms:
            params["search"] = "+AND+".join(search_terms)
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL_RECALL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "drug": drug_name or "unknown",
                    "recall": result,
                    "source": "openfda_recall",
                    "metadata": {
                        "recall_number": result.get("recall_number"),
                        "reason_for_recall": result.get("reason_for_recall"),
                        "status": result.get("status"),
                        "recall_initiation_date": result.get("recall_initiation_date"),
                    }
                })
            
            return results
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Error fetching OpenFDA recalls: {str(e)}")
            return []

