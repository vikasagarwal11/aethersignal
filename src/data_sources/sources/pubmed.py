"""
PubMed API Client.
Fetches adverse event mentions from PubMed literature.
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime
import time

from ..base import SourceClientBase


class PubMedClient(SourceClientBase):
    """
    Client for PubMed API (NCBI E-utilities).
    Free, no authentication required (but API key optional for higher rate limits).
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv("PUBMED_API_KEY")
        self.email = os.getenv("PUBMED_EMAIL", "user@example.com")  # Required by NCBI
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse event mentions from PubMed.
        
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
        
        reaction = query.get("reaction")
        limit = query.get("limit", 50)
        
        # Build search query
        search_terms = [drug_name, "adverse", "event", "side", "effect"]
        if reaction:
            search_terms.append(reaction)
        
        search_query = "+AND+".join(search_terms)
        
        # Step 1: Search PubMed
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": min(limit, 100),
            "retmode": "json",
            "email": self.email
        }
        
        if self.api_key:
            search_params["api_key"] = self.api_key
        
        search_response = requests.get(search_url, params=search_params, timeout=20)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []
        
        # Step 2: Fetch article details
        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids[:limit]),
            "retmode": "xml",
            "email": self.email
        }
        
        if self.api_key:
            fetch_params["api_key"] = self.api_key
        
        # Rate limiting (NCBI requires delay)
        time.sleep(0.34)  # 3 requests per second max
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_response.raise_for_status()
        
        # Parse XML (simplified - would use proper XML parser in production)
        results = self._parse_pubmed_xml(fetch_response.text, drug_name, reaction)
        
        return results
    
    def _parse_pubmed_xml(self, xml_text: str, drug_name: str, reaction: str = None) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response.
        Simplified parser - in production would use proper XML library.
        
        Args:
            xml_text: XML response from PubMed
            drug_name: Drug name
            reaction: Reaction term (optional)
        
        Returns:
            List of normalized entries
        """
        # Simplified parsing - extract basic info
        # In production, use xml.etree.ElementTree or lxml
        results = []
        
        # For now, return basic structure
        # Full implementation would parse XML properly
        entries = xml_text.split("<PubmedArticle>")[1:]  # Simple split
        
        for entry in entries[:50]:  # Limit to 50
            # Extract title (simplified)
            title_start = entry.find("<ArticleTitle>")
            title_end = entry.find("</ArticleTitle>")
            title = entry[title_start+14:title_end] if title_start > 0 and title_end > 0 else "PubMed Article"
            
            # Extract date (simplified)
            date_start = entry.find("<PubDate>")
            date_text = ""
            if date_start > 0:
                year_start = entry.find("<Year>", date_start)
                year_end = entry.find("</Year>", year_start)
                if year_start > 0 and year_end > 0:
                    date_text = entry[year_start+6:year_end]
            
            results.append({
                "timestamp": f"{date_text}-01-01" if date_text else None,
                "drug": drug_name,
                "reaction": reaction,
                "confidence": 0.7,  # Literature mentions are less certain than reports
                "severity": 0.0,  # Can't determine from abstract
                "text": title[:500],  # Truncate long titles
                "source": "pubmed",
                "metadata": {
                    "type": "literature",
                    "full_text_available": False
                }
            })
        
        return results

