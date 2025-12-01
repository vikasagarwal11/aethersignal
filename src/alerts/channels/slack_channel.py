"""
Slack Alert Channel (Phase 2E.3)
Sends alerts to Slack via webhook.
"""

import os
import requests
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SlackChannel:
    """
    Slack alert delivery channel.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Slack channel.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert to Slack.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Dictionary with delivery status
        """
        if not self.webhook_url:
            return {"status": "error", "error": "Slack webhook URL not configured"}
        
        try:
            # Create Slack message payload
            payload = self._create_slack_payload(alert)
            
            # Send to Slack
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {"status": "sent", "channel": "slack"}
        except Exception as e:
            logger.error(f"Slack send error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _create_slack_payload(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack webhook payload."""
        alert_type = alert.get("alert_type", "alert")
        drug = alert.get("drug", "Unknown")
        reaction = alert.get("reaction", "Unknown")
        quantum_score = alert.get("quantum_score", 0.0)
        summary = alert.get("summary", "")
        
        # Color coding
        colors = {
            "high_priority": "#FF0000",  # Red
            "burst": "#FFA500",  # Orange
            "novel_ae": "#0000FF",  # Blue
            "watchlist": "#FFFF00"  # Yellow
        }
        
        color = colors.get(alert_type, "#808080")
        
        return {
            "text": f"🚨 AetherSignal Alert: {drug} → {reaction}",
            "attachments": [
                {
                    "color": color,
                    "title": f"{alert_type.replace('_', ' ').title()} Alert",
                    "fields": [
                        {
                            "title": "Quantum Score",
                            "value": f"{quantum_score:.2f}",
                            "short": True
                        },
                        {
                            "title": "Summary",
                            "value": summary,
                            "short": False
                        }
                    ],
                    "footer": "AetherSignal",
                    "ts": int(datetime.fromisoformat(alert.get("timestamp", "")).timestamp()) if alert.get("timestamp") else None
                }
            ]
        }

