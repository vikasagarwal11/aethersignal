"""
Security Module - Wave 6
License management and feature-based access control
"""

from .license_manager import LicenseManager
from .feature_gate import require_feature, check_feature, render_feature_gate_message

__all__ = [
    "LicenseManager",
    "require_feature",
    "check_feature",
    "render_feature_gate_message"
]

