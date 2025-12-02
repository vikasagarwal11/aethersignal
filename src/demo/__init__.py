"""
Demo Module - Public demo portal components
Wave 4: Public Demo Portal
"""

from .demo_mode import is_demo_mode, enforce_demo_mode, exit_demo_mode
from .demo_loader import load_demo_data

__all__ = [
    "is_demo_mode",
    "enforce_demo_mode",
    "exit_demo_mode",
    "load_demo_data"
]

