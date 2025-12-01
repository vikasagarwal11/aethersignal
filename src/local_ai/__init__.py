"""
Local AI Processing Engines (CHUNK 6.24, 6.26)
Browser-based AI/ML modules for offline processing.

These modules work with both pandas DataFrames (if available) and 
lightweight list-of-dicts data structures for Pyodide compatibility.
"""
try:
    from .case_clustering import LocalCaseClustering
    from .duplicate_signal_detector import LocalDuplicateSignalDetector
    __all__ = [
        "LocalCaseClustering",
        "LocalDuplicateSignalDetector"
    ]
except ImportError:
    __all__ = []

