"""
Config Module - Wave 6
Pricing tiers and configuration management
"""

from .pricing_tiers import (
    PRICING_TIERS,
    get_tier_features,
    get_tier_limits,
    is_feature_in_tier,
    get_tier_info
)

__all__ = [
    "PRICING_TIERS",
    "get_tier_features",
    "get_tier_limits",
    "is_feature_in_tier",
    "get_tier_info"
]

