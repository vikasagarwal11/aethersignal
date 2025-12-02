"""
Feature Gate - Wave 6
Decorator and utilities for feature-based access control
"""

import streamlit as st
import functools
import logging
from typing import Callable, Any
from src.security.license_manager import LicenseManager

logger = logging.getLogger(__name__)


def require_feature(feature: str):
    """
    Decorator to require a specific feature for a function.
    
    Args:
        feature: Feature name to require
    
    Usage:
        @require_feature("executive_dashboard")
        def show_dashboard():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            lm = LicenseManager()
            
            if not lm.feature_available(feature):
                st.error(f"🔒 **Feature '{feature}' is not available in your plan.**")
                st.info(
                    f"💡 This feature requires a **Pro** or **Enterprise** plan. "
                    f"Please upgrade or contact sales for access."
                )
                
                # Show upgrade button
                if st.button("💳 View Plans", key=f"upgrade_{feature}"):
                    st.switch_page("pages/Billing.py")
                
                return None
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_feature(feature: str) -> bool:
    """
    Check if a feature is available (non-blocking).
    
    Args:
        feature: Feature name
    
    Returns:
        True if feature is available
    """
    try:
        lm = LicenseManager()
        return lm.feature_available(feature)
    except Exception as e:
        logger.error(f"Error checking feature: {e}")
        return False


def render_feature_gate_message(feature: str, custom_message: str = None) -> None:
    """
    Render a feature gate message in the UI.
    
    Args:
        feature: Feature name
        custom_message: Optional custom message
    """
    if check_feature(feature):
        return  # Feature is available, no message needed
    
    # Check if pricing is disabled
    try:
        from src.utils.config_loader import get_config_value
        if not get_config_value("enable_pricing", False):
            # Pricing disabled = all features available, so this shouldn't happen
            return
    except Exception:
        pass
    
    message = custom_message or f"🔒 **Feature '{feature}' is not available in your plan.**"
    st.warning(message)
    
    st.info(
        f"💡 This feature requires a **Pro** or **Enterprise** plan. "
        f"Please upgrade or contact sales for access."
    )
    
    if st.button("💳 View Plans", key=f"upgrade_gate_{feature}"):
        st.switch_page("pages/Billing.py")

