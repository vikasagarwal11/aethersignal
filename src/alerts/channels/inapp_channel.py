"""
In-App Alert Channel (Phase 2E.5)
Stores alerts for in-app notification display.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class InAppChannel:
    """
    In-app alert delivery channel.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize in-app channel.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.notifications_store = []  # In-memory store
    
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store alert for in-app display.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Dictionary with delivery status
        """
        try:
            # Store notification
            notification = {
                "alert_id": alert.get("alert_id"),
                "timestamp": alert.get("timestamp"),
                "type": alert.get("alert_type"),
                "severity": alert.get("severity"),
                "drug": alert.get("drug"),
                "reaction": alert.get("reaction"),
                "summary": alert.get("summary"),
                "quantum_score": alert.get("quantum_score"),
                "read": False
            }
            
            self.notifications_store.append(notification)
            
            return {"status": "stored", "channel": "inapp", "alert_id": alert.get("alert_id")}
        except Exception as e:
            logger.error(f"In-app channel error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_notifications(self, unread_only: bool = True) -> list:
        """Get notifications."""
        notifications = self.notifications_store
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        return notifications
    
    def mark_read(self, alert_id: str):
        """Mark notification as read."""
        for notification in self.notifications_store:
            if notification.get("alert_id") == alert_id:
                notification["read"] = True
                break

