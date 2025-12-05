"""
Analytics Module - Multi-Dimensional AE Explorer & PivotCube
"""

from .pivot_cube import PivotCube

# Import from analytics.py module if it exists
try:
    import sys
    from pathlib import Path
    analytics_module_path = Path(__file__).parent.parent / "analytics.py"
    if analytics_module_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("analytics_module", analytics_module_path)
        analytics_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analytics_module)
        # Export analytics module attributes
        ANALYTICS_STORAGE_AVAILABLE = getattr(analytics_module, 'ANALYTICS_STORAGE_AVAILABLE', False)
        ANALYTICS_DIR = getattr(analytics_module, 'ANALYTICS_DIR', None)
        USAGE_LOG_FILE = getattr(analytics_module, 'USAGE_LOG_FILE', None)
        STATS_FILE = getattr(analytics_module, 'STATS_FILE', None)
        init_session_id = getattr(analytics_module, 'init_session_id', lambda: "anonymous")
        log_event = getattr(analytics_module, 'log_event', lambda *args, **kwargs: None)
        get_usage_stats = getattr(analytics_module, 'get_usage_stats', lambda: {})
    else:
        # Fallback values
        ANALYTICS_STORAGE_AVAILABLE = False
        ANALYTICS_DIR = None
        USAGE_LOG_FILE = None
        STATS_FILE = None
        init_session_id = lambda: "anonymous"
        log_event = lambda *args, **kwargs: None
        get_usage_stats = lambda: {}
except Exception:
    ANALYTICS_STORAGE_AVAILABLE = False
    ANALYTICS_DIR = None
    USAGE_LOG_FILE = None
    STATS_FILE = None
    init_session_id = lambda: "anonymous"
    log_event = lambda *args, **kwargs: None
    get_usage_stats = lambda: {}

__all__ = [
    "PivotCube",
    "ANALYTICS_STORAGE_AVAILABLE",
    "ANALYTICS_DIR",
    "USAGE_LOG_FILE",
    "STATS_FILE",
    "init_session_id",
    "log_event",
    "get_usage_stats"
]

