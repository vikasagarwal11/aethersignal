"""
Email Alert Channel (Phase 2E.2)
Sends alerts via email (SMTP).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmailChannel:
    """
    Email alert delivery channel.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email channel.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("ALERTS_FROM_EMAIL", self.smtp_user)
        self.to_emails = os.getenv("ALERTS_TO_EMAILS", "").split(",")
    
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert via email.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            Dictionary with delivery status
        """
        if not self.smtp_user or not self.smtp_password:
            return {"status": "error", "error": "SMTP credentials not configured"}
        
        if not self.to_emails or not self.to_emails[0]:
            return {"status": "error", "error": "No recipient emails configured"}
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._generate_subject(alert)
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            
            # Create HTML body
            html_body = self._generate_html_body(alert)
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {"status": "sent", "channel": "email"}
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _generate_subject(self, alert: Dict[str, Any]) -> str:
        """Generate email subject."""
        alert_type = alert.get("alert_type", "alert")
        drug = alert.get("drug", "Unknown")
        reaction = alert.get("reaction", "Unknown")
        quantum_score = alert.get("quantum_score", 0.0)
        
        emoji = {
            "high_priority": "🚨",
            "burst": "📈",
            "novel_ae": "🧪",
            "watchlist": "⚠️"
        }.get(alert_type, "⚠️")
        
        return f"{emoji} AetherSignal {alert_type.replace('_', ' ').title()}: {drug} → {reaction} (QuantumScore: {quantum_score:.2f})"
    
    def _generate_html_body(self, alert: Dict[str, Any]) -> str:
        """Generate HTML email body."""
        drug = alert.get("drug", "Unknown")
        reaction = alert.get("reaction", "Unknown")
        quantum_score = alert.get("quantum_score", 0.0)
        summary = alert.get("summary", "")
        suggested_action = alert.get("suggested_action", "")
        
        consensus = alert.get("consensus", {})
        source_count = consensus.get("source_count", 0)
        sources = ", ".join(alert.get("sources", []))
        
        html = f"""
        <html>
        <body>
            <h2>AetherSignal Alert</h2>
            <p><strong>Drug:</strong> {drug}</p>
            <p><strong>Reaction:</strong> {reaction}</p>
            <p><strong>Quantum Score:</strong> {quantum_score:.2f}</p>
            <p><strong>Summary:</strong> {summary}</p>
            <p><strong>Sources:</strong> {sources} ({source_count} total)</p>
            <p><strong>Suggested Action:</strong> {suggested_action}</p>
            <hr>
            <p><small>This is an automated alert from AetherSignal.</small></p>
        </body>
        </html>
        """
        return html

