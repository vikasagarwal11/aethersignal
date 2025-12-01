"""
Global Lineage Tracker Instance - Phase 3L Step 2
Shared lineage tracker instance for all modules.
"""

from .lineage_tracker import LineageTracker
from .config import LINEAGE_ENABLED

# Global lineage tracker instance (shared across all modules)
_lineage_tracker: LineageTracker = None


def get_lineage_tracker() -> LineageTracker:
    """
    Get or create global lineage tracker instance.
    
    Returns:
        LineageTracker instance
    """
    global _lineage_tracker
    
    if not LINEAGE_ENABLED:
        # Return a no-op tracker if disabled
        class NoOpTracker:
            def record(self, *args, **kwargs):
                return {}
            def get_lineage(self, *args, **kwargs):
                return []
            def get_lineage_chain(self, *args, **kwargs):
                return {}
        
        return NoOpTracker()
    
    if _lineage_tracker is None:
        _lineage_tracker = LineageTracker()
    
    return _lineage_tracker


# Convenience function for easy access
def record_lineage(record_id: str, stage: str, metadata: dict = None):
    """Convenience function to record lineage event."""
    tracker = get_lineage_tracker()
    return tracker.record(record_id, stage, metadata)

