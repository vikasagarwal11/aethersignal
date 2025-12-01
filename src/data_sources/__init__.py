"""
Data Sources Module - Unified ingestion architecture for all AE data sources.
"""

from .safe_executor import SafeExecutor, RetryConfig, safe_fetch, safe_request
from .data_source_manager import DataSourceManager, DataSourceConfig, FallbackMode
from .data_source_manager_v2 import DataSourceManagerV2
from .base import SourceClientBase
from .registry import SourceRegistry

__all__ = [
    "SafeExecutor",
    "RetryConfig",
    "safe_fetch",
    "safe_request",
    "DataSourceManager",
    "DataSourceManagerV2",
    "DataSourceConfig",
    "FallbackMode",
    "SourceClientBase",
    "SourceRegistry",
]

