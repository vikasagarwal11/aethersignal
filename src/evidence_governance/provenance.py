"""
Provenance Module - Phase 3L Step 3
Exports ProvenanceTracker (registry) and ProvenanceEngine (scoring).
"""

from .provenance_engine import ProvenanceEngine
from .provenance_tracker import ProvenanceTracker

# Global instances
_provenance_engine: ProvenanceEngine = None
_provenance_tracker: ProvenanceTracker = None


def get_provenance_engine() -> ProvenanceEngine:
    """Get or create global provenance engine instance."""
    global _provenance_engine
    if _provenance_engine is None:
        _provenance_engine = ProvenanceEngine()
    return _provenance_engine


def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create global provenance tracker instance."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceTracker()
    return _provenance_tracker


# Convenience function
def get_provenance() -> ProvenanceEngine:
    """Convenience function to get provenance engine."""
    return get_provenance_engine()


