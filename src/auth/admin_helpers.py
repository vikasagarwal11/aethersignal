"""
Admin Helper Functions - Check super admin status
"""

import streamlit as st
from typing import Optional
from src.auth.user_management import get_user_profile, get_user_role


def is_super_admin(user_id: Optional[str] = None) -> bool:
    """
    Check if current user is a super admin.
    
    Args:
        user_id: Optional user ID to check. If None, uses current session user.
    
    Returns:
        True if user is super admin (role == "admin")
    """
    # Check session state first (faster)
    if user_id is None:
        user_profile = st.session_state.get("user_profile")
        if user_profile:
            role = user_profile.get("role", "scientist")
            return role == "admin" or role == "super_admin"
        
        # Fallback to user_id from session
        user_id = st.session_state.get("user_id")
    
    if not user_id:
        return False
    
    # Get role from database
    role = get_user_role(user_id)
    return role == "admin" or role == "super_admin"


def require_super_admin():
    """
    Require super admin access. Raises error if not admin.
    
    Raises:
        PermissionError: If user is not super admin
    """
    if not is_super_admin():
        raise PermissionError("Super admin access required. This feature is only available to administrators.")


def get_current_user_id() -> Optional[str]:
    """
    Get current user ID from session.
    
    Returns:
        User ID or None
    """
    return st.session_state.get("user_id") or (st.session_state.get("user_profile", {}).get("id") if st.session_state.get("user_profile") else None)

