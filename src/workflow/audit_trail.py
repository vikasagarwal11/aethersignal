"""
Audit Trail System (Phase 3H.5)
21 CFR Part 11-compatible audit logging.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuditTrail:
    """
    21 CFR Part 11-compatible audit trail.
    """
    
    def __init__(self):
        """Initialize audit trail."""
        self.logs: List[Dict[str, Any]] = []
    
    def log_action(
        self,
        actor: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ai_assist: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an action to audit trail.
        
        Args:
            actor: User/system identifier
            role: User role
            action: Action performed
            entity_type: Type of entity (bundle, task, review, etc.)
            entity_id: Entity ID
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            ai_assist: Whether AI assisted
            metadata: Optional additional metadata
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "role": role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None,
            "ai_assist": ai_assist,
            "metadata": metadata or {}
        }
        
        self.logs.append(log_entry)
        
        # In production, would also write to database
        logger.info(f"Audit log: {action} by {actor} on {entity_type} {entity_id}")
    
    def get_audit_log(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries with filters.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            actor: Filter by actor
            action: Filter by action
            limit: Maximum results
        
        Returns:
            List of audit log entries
        """
        filtered = self.logs
        
        if entity_type:
            filtered = [l for l in filtered if l.get("entity_type") == entity_type]
        
        if entity_id:
            filtered = [l for l in filtered if l.get("entity_id") == entity_id]
        
        if actor:
            filtered = [l for l in filtered if l.get("actor") == actor]
        
        if action:
            filtered = [l for l in filtered if l.get("action") == action]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return filtered[:limit]
    
    def get_entity_history(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Get complete history for an entity."""
        return self.get_audit_log(entity_type=entity_type, entity_id=entity_id)
    
    def export_audit_log(
        self,
        format: str = "json"
    ) -> str:
        """
        Export audit log.
        
        Args:
            format: Export format (json, csv)
        
        Returns:
            Exported audit log as string
        """
        if format == "json":
            import json
            return json.dumps(self.logs, indent=2)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if self.logs:
                writer = csv.DictWriter(output, fieldnames=self.logs[0].keys())
                writer.writeheader()
                writer.writerows(self.logs)
            return output.getvalue()
        else:
            return str(self.logs)

