"""
Quality Module - Phase 3L Step 4
Exports DataQualityEngine.
"""

from .quality_engine import DataQualityEngine

# Global instance
_quality_engine: DataQualityEngine = None


def get_quality_engine() -> DataQualityEngine:
    """Get or create global quality engine instance."""
    global _quality_engine
    if _quality_engine is None:
        _quality_engine = DataQualityEngine()
    return _quality_engine


# Convenience function
def get_quality() -> DataQualityEngine:
    """Convenience function to get quality engine."""
    return get_quality_engine()

