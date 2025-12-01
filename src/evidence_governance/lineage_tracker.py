"""
Lineage Tracker - Phase 3L Step 1
Tracks every transformation from raw → cleaned → mapped → stored → dashboard.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from .config import LINEAGE_ENABLED, LINEAGE_STORAGE, ensure_directories

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    Tracks data lineage through all transformation stages.
    """
    
    # Transformation stages
    STAGES = [
        "ingestion",      # Raw data received
        "cleaning",       # Data cleaned
        "normalization",  # Data normalized
        "mapping",        # Mapped to unified schema
        "scoring",        # Scores calculated
        "storage",        # Stored in database
        "aggregation",    # Aggregated for dashboard
        "visualization"   # Rendered in UI
    ]
    
    def __init__(self):
        """Initialize lineage tracker."""
        self.events: List[Dict[str, Any]] = []
        self.storage_file = LINEAGE_STORAGE / "lineage_events.jsonl"
        
        if LINEAGE_ENABLED:
            ensure_directories()
            self._load_existing_events()
    
    def record(
        self,
        record_id: str,
        stage: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Record a lineage event.
        
        Args:
            record_id: Unique record identifier
            stage: Transformation stage
            metadata: Optional metadata about the transformation
            parent_ids: Optional list of parent record IDs
        
        Returns:
            Lineage event dictionary
        """
        if not LINEAGE_ENABLED:
            return {}
        
        if stage not in self.STAGES:
            logger.warning(f"Unknown stage: {stage}")
        
        event = {
            "lineage_event_id": str(uuid.uuid4()),
            "record_id": record_id,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "parent_ids": parent_ids or []
        }
        
        self.events.append(event)
        
        # Persist to file
        try:
            with open(self.storage_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Error persisting lineage event: {e}")
        
        return event
    
    def get_lineage(self, record_id: str) -> List[Dict[str, Any]]:
        """
        Get complete lineage for a record.
        
        Args:
            record_id: Record identifier
        
        Returns:
            List of lineage events (chronologically ordered)
        """
        if not LINEAGE_ENABLED:
            return []
        
        lineage = [e for e in self.events if e["record_id"] == record_id]
        lineage.sort(key=lambda x: x["timestamp"])
        
        return lineage
    
    def get_lineage_chain(self, record_id: str) -> Dict[str, Any]:
        """
        Get lineage chain with parent relationships.
        
        Args:
            record_id: Record identifier
        
        Returns:
            Lineage chain dictionary
        """
        if not LINEAGE_ENABLED:
            return {}
        
        lineage = self.get_lineage(record_id)
        
        if not lineage:
            return {}
        
        chain = {
            "record_id": record_id,
            "stages": lineage,
            "first_stage": lineage[0] if lineage else None,
            "last_stage": lineage[-1] if lineage else None,
            "total_stages": len(lineage)
        }
        
        return chain
    
    def _load_existing_events(self):
        """Load existing lineage events from storage."""
        if not self.storage_file.exists():
            return
        
        try:
            with open(self.storage_file, "r") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        self.events.append(event)
            
            logger.info(f"Loaded {len(self.events)} lineage events")
        except Exception as e:
            logger.error(f"Error loading lineage events: {e}")
    
    def get_all_lineage(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all lineage events (for admin/debugging).
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of lineage events
        """
        if not LINEAGE_ENABLED:
            return []
        
        return self.events[-limit:]

