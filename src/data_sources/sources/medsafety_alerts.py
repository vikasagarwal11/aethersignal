"""
MedSafetyAlerts API Client.
Fetches drug safety alerts from FDA MedWatch and EMA RSS feeds.
"""

import os
import requests
import feedparser
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..base import SourceClientBase
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)


class MedSafetyAlertsClient(SourceClientBase):
    """
    Client for FDA MedWatch and EMA Safety Alerts (RSS feeds).
    Free, no authentication required.
    
    Sources:
    - FDA MedWatch RSS: https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program
    - EMA Safety Updates: RSS feed from EMA website
    """
    
    FDA_MEDWATCH_RSS = "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/safety-alerts-medwatch"
    EMA_SAFETY_RSS = "https://www.ema.europa.eu/en/medicines/regulatory-procedures-guidelines/rss.xml"
    HEALTH_CANADA_RSS = "https://www.canada.ca/en/health-canada/services/drugs-health-products/medeffect-canada.html"
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.fda_enabled = config.get("fda_enabled", True)
        self.ema_enabled = config.get("ema_enabled", True)
        self.health_canada_enabled = config.get("health_canada_enabled", True)
    
    def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch drug safety alerts from RSS feeds.
        
        Args:
            query: Query parameters
                - drug_name: Drug name to filter (optional)
                - limit: Number of results (default: 50)
                - days_back: Days back to search (default: 30)
        
        Returns:
            List of normalized alert entries
        """
        drug_name = query.get("drug_name") or query.get("drug")
        limit = query.get("limit", 50)
        days_back = query.get("days_back", 30)
        
        all_alerts = []
        
        # Fetch from FDA MedWatch
        if self.fda_enabled:
            try:
                fda_alerts = self._fetch_fda_alerts(drug_name, days_back, limit)
                all_alerts.extend(fda_alerts)
            except Exception as e:
                logger.warning(f"Error fetching FDA alerts: {str(e)}")
        
        # Fetch from EMA
        if self.ema_enabled:
            try:
                ema_alerts = self._fetch_ema_alerts(drug_name, days_back, limit)
                all_alerts.extend(ema_alerts)
            except Exception as e:
                logger.warning(f"Error fetching EMA alerts: {str(e)}")
        
        # Fetch from Health Canada
        if self.health_canada_enabled:
            try:
                canada_alerts = self._fetch_health_canada_alerts(drug_name, days_back, limit)
                all_alerts.extend(canada_alerts)
            except Exception as e:
                logger.warning(f"Error fetching Health Canada alerts: {str(e)}")
        
        # Sort by date (newest first) and limit
        all_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_alerts[:limit]
    
    def _fetch_fda_alerts(self, drug_name: Optional[str], days_back: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch FDA MedWatch alerts from RSS feed."""
        alerts = []
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(self.FDA_MEDWATCH_RSS)
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries[:limit * 2]:  # Get more to filter
                # Extract date
                entry_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                
                if entry_date < cutoff_date:
                    continue
                
                # Extract text
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                
                # Filter by drug name if provided
                if drug_name:
                    drug_lower = drug_name.lower()
                    if drug_lower not in title.lower() and drug_lower not in summary.lower():
                        continue
                
                # Extract drug mentions (simple keyword extraction)
                drugs_mentioned = self._extract_drug_mentions(title + " " + summary)
                
                alerts.append({
                    "timestamp": entry_date.isoformat(),
                    "drug": drug_name or drugs_mentioned[0] if drugs_mentioned else "unknown",
                    "drugs_mentioned": drugs_mentioned,
                    "reaction": None,  # Alerts don't always specify reactions
                    "confidence": 1.0,  # Regulatory alerts are authoritative
                    "severity": 0.8,  # Alerts are typically serious
                    "text": f"{title}\n\n{summary}",
                    "source": "fda_medwatch",
                    "metadata": {
                        "alert_type": "safety_alert",
                        "link": link,
                        "authority": "FDA",
                        "raw_entry": {
                            "title": title,
                            "summary": summary,
                            "published": entry.get("published", "")
                        }
                    }
                })
        
        except Exception as e:
            logger.error(f"Error parsing FDA RSS feed: {str(e)}")
        
        return alerts
    
    def _fetch_ema_alerts(self, drug_name: Optional[str], days_back: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch EMA safety alerts from RSS feed."""
        alerts = []
        
        try:
            feed = feedparser.parse(self.EMA_SAFETY_RSS)
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries[:limit * 2]:
                entry_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                
                if entry_date < cutoff_date:
                    continue
                
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                
                if drug_name:
                    drug_lower = drug_name.lower()
                    if drug_lower not in title.lower() and drug_lower not in summary.lower():
                        continue
                
                drugs_mentioned = self._extract_drug_mentions(title + " " + summary)
                
                alerts.append({
                    "timestamp": entry_date.isoformat(),
                    "drug": drug_name or drugs_mentioned[0] if drugs_mentioned else "unknown",
                    "drugs_mentioned": drugs_mentioned,
                    "reaction": None,
                    "confidence": 1.0,
                    "severity": 0.8,
                    "text": f"{title}\n\n{summary}",
                    "source": "ema_safety",
                    "metadata": {
                        "alert_type": "safety_update",
                        "link": link,
                        "authority": "EMA",
                        "raw_entry": {
                            "title": title,
                            "summary": summary,
                            "published": entry.get("published", "")
                        }
                    }
                })
        
        except Exception as e:
            logger.error(f"Error parsing EMA RSS feed: {str(e)}")
        
        return alerts
    
    def _fetch_health_canada_alerts(self, drug_name: Optional[str], days_back: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch Health Canada alerts (placeholder - may need web scraping)."""
        # Health Canada doesn't have a clean RSS feed, would need web scraping
        # For now, return empty list - can be enhanced later
        return []
    
    def _extract_drug_mentions(self, text: str) -> List[str]:
        """Extract drug names from text (simple keyword matching)."""
        # Common drug name patterns
        # In production, would use NER or drug dictionary
        drugs = []
        text_lower = text.lower()
        
        # Common drug names to look for
        common_drugs = [
            "ozempic", "wegovy", "mounjaro", "semaglutide", "tirzepatide",
            "adderall", "vyvanse", "ritalin", "concerta",
            "prozac", "zoloft", "lexapro", "cymbalta",
            "finasteride", "accutane", "humira", "keytruda"
        ]
        
        for drug in common_drugs:
            if drug in text_lower:
                drugs.append(drug)
        
        return drugs[:5]  # Limit to 5 drugs per alert

