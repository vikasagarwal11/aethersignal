"""
Executive Dashboard Module - Phase 3J
Global Drug Safety Executive Dashboard for VPs, Heads of Safety, Clinical, Regulatory.
"""

from .dashboard import render_executive_dashboard
from .loaders import load_unified_ae_data
from .aggregator import ExecutiveAggregator

__all__ = [
    "render_executive_dashboard",
    "load_unified_ae_data",
    "ExecutiveAggregator"
]

