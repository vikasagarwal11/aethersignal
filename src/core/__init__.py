"""
Core module for AetherSignal.
Contains foundational data models and structures used across the platform.
"""
from typing import Optional

# Import timeline model
try:
    from src.core.timeline_model import (
        TimelineEvent,
        SignalLifecycleTimeline
    )
    TIMELINE_MODEL_AVAILABLE = True
except ImportError:
    TIMELINE_MODEL_AVAILABLE = False
    TimelineEvent = None
    SignalLifecycleTimeline = None

# Import lifecycle event extractor
try:
    from src.core.lifecycle_event_extractor import (
        LifecycleEventExtractor
    )
    EXTRACTOR_AVAILABLE = True
except ImportError:
    EXTRACTOR_AVAILABLE = False
    LifecycleEventExtractor = None

__all__ = [
    "TimelineEvent",
    "SignalLifecycleTimeline",
    "LifecycleEventExtractor",
    "TIMELINE_MODEL_AVAILABLE",
    "EXTRACTOR_AVAILABLE"
]
