"""
API Alert Channel (Phase 2E.5)
Stores alerts in database/API for retrieval.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIChannel:
    """
    API alert delivery channel (stores alerts for API retrieval).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize API channel.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.alerts_store = []  # In-memory store (would use database in production)
    
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store alert for API retrieval.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Dictionary with delivery status
        """
        try:
            # Store alert
            self.alerts_store.append(alert)
            
            # In production, would store in database
            # db.store_alert(alert)
            
            return {"status": "stored", "channel": "api", "alert_id": alert.get("alert_id")}
        except Exception as e:
            logger.error(f"API channel error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_alerts(
        self,
        limit: int = 100,
        alert_type: str = None,
        drug: str = None
    ) -> list:
        """Get stored alerts."""
        alerts = self.alerts_store
        
        if alert_type:
            alerts = [a for a in alerts if a.get("alert_type") == alert_type]
        
        if drug:
            alerts = [a for a in alerts if drug.lower() in a.get("drug", "").lower()]
        
        return alerts[-limit:]

