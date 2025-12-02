"""
License Manager - Wave 6
Manages license keys, tier validation, and feature access
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any
from src.config.pricing_tiers import is_feature_in_tier, get_tier_info
from src.utils.config_loader import get_config_value

logger = logging.getLogger(__name__)


class LicenseManager:
    """
    Manages license keys and tier-based feature access.
    """
    
    def __init__(self):
        """Initialize license manager."""
        self.license_info = st.session_state.get("license_info", None)
    
    def load_license(self, license_key: str) -> Dict[str, Any]:
        """
        Load and validate a license key.
        
        Args:
            license_key: License key string
        
        Returns:
            License info dictionary
        """
        # In production, this would validate against a license server
        # For now, we use pattern-based detection
        
        license_key = license_key.strip().upper()
        
        # Determine tier from license key pattern
        if license_key.startswith("ENT-") or license_key.startswith("ENTERPRISE-"):
            tier = "enterprise"
        elif license_key.startswith("PRO-") or license_key.startswith("PROFESSIONAL-"):
            tier = "pro"
        elif license_key.startswith("STARTER-") or license_key.startswith("ST-"):
            tier = "starter"
        elif license_key == "DEMO" or license_key.startswith("DEMO-"):
            tier = "starter"  # Demo uses starter tier
        else:
            # Default to starter for unknown keys
            tier = "starter"
            logger.warning(f"Unknown license key pattern, defaulting to starter: {license_key[:10]}...")
        
        license_info = {
            "license_key": license_key,
            "tier": tier,
            "activated": True,
            "activated_at": None  # Would be timestamp in production
        }
        
        st.session_state["license_info"] = license_info
        self.license_info = license_info
        
        logger.info(f"License loaded: tier={tier}")
        
        return license_info
    
    def get_tier(self) -> str:
        """
        Get current license tier.
        
        Returns:
            Tier name ("starter", "pro", "enterprise")
        """
        if not self.license_info:
            # Check session state
            self.license_info = st.session_state.get("license_info", None)
        
        if not self.license_info:
            return "starter"  # Default tier
        
        return self.license_info.get("tier", "starter")
    
    def feature_available(self, feature: str) -> bool:
        """
        Check if a feature is available in current tier.
        
        Args:
            feature: Feature name
        
        Returns:
            True if feature is available
        """
        # If pricing is disabled, all features are available
        if not get_config_value("enable_pricing", False):
            return True
        
        tier = self.get_tier()
        return is_feature_in_tier(tier, feature)
    
    def is_pricing_enabled(self) -> bool:
        """
        Check if pricing system is enabled.
        
        Returns:
            True if pricing is enabled
        """
        return get_config_value("enable_pricing", False)
    
    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current license information.
        
        Returns:
            License info dictionary or None
        """
        return self.license_info or st.session_state.get("license_info", None)
    
    def is_activated(self) -> bool:
        """
        Check if license is activated.
        
        Returns:
            True if license is activated
        """
        info = self.get_license_info()
        return info is not None and info.get("activated", False)
    
    def clear_license(self) -> None:
        """Clear license from session state."""
        if "license_info" in st.session_state:
            del st.session_state["license_info"]
        self.license_info = None
        logger.info("License cleared")

