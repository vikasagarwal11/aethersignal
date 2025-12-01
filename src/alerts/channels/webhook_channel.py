"""
Webhook Alert Channel (Phase 2E.4)
Sends alerts to external webhook endpoints.
"""

import os
import requests
import hmac
import hashlib
import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class WebhookChannel:
    """
    Webhook alert delivery channel.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize webhook channel.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.webhook_urls = os.getenv("WEBHOOK_URLS", "").split(",")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
    
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert to webhook endpoints.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Dictionary with delivery status
        """
        if not self.webhook_urls or not self.webhook_urls[0]:
            return {"status": "error", "error": "No webhook URLs configured"}
        
        results = []
        
        for url in self.webhook_urls:
            url = url.strip()
            if not url:
                continue
            
            try:
                # Create payload
                payload = self._create_webhook_payload(alert)
                
                # Add HMAC signature if secret is configured
                headers = {"Content-Type": "application/json"}
                if self.webhook_secret:
                    signature = self._generate_signature(payload, self.webhook_secret)
                    headers["X-AetherSignal-Signature"] = signature
                
                # Send to webhook
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                
                results.append({"url": url, "status": "sent"})
            except Exception as e:
                logger.error(f"Webhook send error to {url}: {str(e)}")
                results.append({"url": url, "status": "error", "error": str(e)})
        
        return {"status": "sent", "channel": "webhook", "results": results}
    
    def _create_webhook_payload(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook payload."""
        return {
            "alert_id": alert.get("alert_id"),
            "timestamp": alert.get("timestamp"),
            "drug": alert.get("drug"),
            "reaction": alert.get("reaction"),
            "alert_type": alert.get("alert_type"),
            "severity": alert.get("severity"),
            "quantum_score": alert.get("quantum_score"),
            "components": alert.get("components", {}),
            "consensus": alert.get("consensus", {}),
            "novelty": alert.get("novelty", {}),
            "sources": alert.get("sources", []),
            "source_count": alert.get("source_count", 0),
            "total_cases": alert.get("total_cases", 0),
            "summary": alert.get("summary"),
            "suggested_action": alert.get("suggested_action")
        }
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

