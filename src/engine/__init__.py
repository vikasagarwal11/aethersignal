"""
Engine module for hybrid computation mode management.

This module provides:
- Hybrid Mode Manager: EXACT/HYBRID/APPROX mode selection
- Dataset Profiler: Dataset analysis for mode selection
- Browser Capability Detector: Hardware/browser capability detection
- Mode-Aware Pipeline: Query routing based on mode decisions
"""
from typing import Optional

# Import main classes
try:
    from src.engine.hybrid_mode_manager import (
        HybridModeManager,
        get_hybrid_mode_manager,
        get_current_computation_mode,
        ComputationMode
    )
    MODE_MANAGER_AVAILABLE = True
except ImportError:
    MODE_MANAGER_AVAILABLE = False
    HybridModeManager = None

try:
    from src.engine.dataset_profiler import (
        profile_dataframe,
        profile_from_file_info,
        estimate_profile_from_sample,
        get_profile_for_mode_selection
    )
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False

try:
    from src.engine.browser_capability_detector import (
        BrowserCapabilityDetector,
        BrowserCapabilities,
        get_browser_capability_detector,
        detect_browser_capabilities,
        get_capability_score
    )
    CAPABILITY_DETECTOR_AVAILABLE = True
except ImportError:
    CAPABILITY_DETECTOR_AVAILABLE = False

try:
    from src.engine.mode_aware_pipeline import (
        ModeAwarePipeline,
        PipelineResult,
        get_mode_aware_pipeline,
        execute_mode_aware_query
    )
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False

__all__ = [
    "HybridModeManager",
    "get_hybrid_mode_manager",
    "get_current_computation_mode",
    "ComputationMode",
    "profile_dataframe",
    "profile_from_file_info",
    "estimate_profile_from_sample",
    "get_profile_for_mode_selection",
    "BrowserCapabilityDetector",
    "BrowserCapabilities",
    "get_browser_capability_detector",
    "detect_browser_capabilities",
    "get_capability_score",
    "ModeAwarePipeline",
    "PipelineResult",
    "get_mode_aware_pipeline",
    "execute_mode_aware_query"
]
