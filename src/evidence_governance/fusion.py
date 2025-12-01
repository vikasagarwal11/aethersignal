"""
Fusion Module - Phase 3L Step 5
Exports EvidenceFusionEngine.
"""

from .fusion_engine import EvidenceFusionEngine

# Global instance
_fusion_engine: EvidenceFusionEngine = None


def get_fusion_engine() -> EvidenceFusionEngine:
    """Get or create global fusion engine instance."""
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = EvidenceFusionEngine()
    return _fusion_engine


# Convenience function
def get_fusion() -> EvidenceFusionEngine:
    """Convenience function to get fusion engine."""
    return get_fusion_engine()

