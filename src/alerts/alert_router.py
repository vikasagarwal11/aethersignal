"""
Alert Router (Phase 2E.1)
Central routing system for alert delivery to multiple channels.
"""

import os
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertRouter:
    """
    Central alert router that dispatches alerts to multiple channels.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize alert router.
        
        Args:
            config: Configuration dictionary with channel settings
        """
        self.config = config or self._load_config()
        self.channels = {}
        self._initialize_channels()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and defaults."""
        return {
            "channels": {
                "email": os.getenv("ALERTS_EMAIL_ENABLED", "false").lower() == "true",
                "slack": os.getenv("ALERTS_SLACK_ENABLED", "false").lower() == "true",
                "webhook": os.getenv("ALERTS_WEBHOOK_ENABLED", "false").lower() == "true",
                "api": True,  # Always enabled
                "inapp": True  # Always enabled
            },
            "thresholds": {
                "high_priority": 0.80,
                "watchlist": 0.45,
                "burst": 0.5,
                "novel_ae": 0.7
            }
        }
    
    def _initialize_channels(self):
        """Initialize channel handlers."""
        from .channels.email_channel import EmailChannel
        from .channels.slack_channel import SlackChannel
        from .channels.webhook_channel import WebhookChannel
        from .channels.api_channel import APIChannel
        from .channels.inapp_channel import InAppChannel
        
        self.channels = {
            "email": EmailChannel(self.config) if self.config["channels"]["email"] else None,
            "slack": SlackChannel(self.config) if self.config["channels"]["slack"] else None,
            "webhook": WebhookChannel(self.config) if self.config["channels"]["webhook"] else None,
            "api": APIChannel(self.config),
            "inapp": InAppChannel(self.config)
        }
    
    def dispatch(
        self,
        alert: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatch alert to enabled channels.
        
        Args:
            alert: Alert dictionary
            channels: Optional list of specific channels to use
        
        Returns:
            Dictionary with delivery status for each channel
        """
        results = {}
        
        # Determine which channels to use
        if channels:
            target_channels = channels
        else:
            # Use alert type to determine channels
            alert_type = alert.get("alert_type", "watchlist")
            target_channels = self._get_channels_for_alert_type(alert_type)
        
        # Dispatch to each channel
        for channel_name in target_channels:
            channel = self.channels.get(channel_name)
            if not channel:
                results[channel_name] = {"status": "disabled", "error": "Channel not enabled"}
                continue
            
            try:
                result = channel.send(alert)
                results[channel_name] = result
            except Exception as e:
                logger.error(f"Error sending alert to {channel_name}: {str(e)}")
                results[channel_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def _get_channels_for_alert_type(self, alert_type: str) -> List[str]:
        """Get channels for alert type."""
        if alert_type == "high_priority":
            return ["email", "slack", "webhook", "api", "inapp"]
        elif alert_type == "burst":
            return ["email", "slack", "api", "inapp"]
        elif alert_type == "novel_ae":
            return ["email", "api", "inapp"]
        else:  # watchlist
            return ["api", "inapp"]

