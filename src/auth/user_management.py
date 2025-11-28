"""
User management module for AetherSignal.
Handles user profiles, roles, and company associations.
"""

import os
import streamlit as st
from typing import Optional, Dict, Any

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase_db() -> Optional[Client]:
    """Get Supabase client for database operations."""
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL")
    # Use service key only in trusted backend contexts; anon key otherwise
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        return None
    
    try:
        return create_client(url, key)
    except Exception:
        return None


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from database.
    
    Args:
        user_id: User UUID
        
    Returns:
        Dictionary with user profile data or None
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    sb = get_supabase_db()
    if not sb:
        return None
    
    try:
        # Query user_profiles table
        response = sb.table("user_profiles").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # If profile doesn't exist, create one from auth user
        from .auth import get_supabase_auth
        auth_sb = get_supabase_auth()
        if auth_sb:
            auth_user = auth_sb.auth.get_user()
            if auth_user.user:
                # Create default profile
                profile = {
                    "id": user_id,
                    "email": auth_user.user.email,
                    "full_name": "",
                    "organization": "",
                    "role": "scientist",
                    "subscription_tier": "free"
                }
                # Try to insert (may fail if RLS prevents it)
                try:
                    sb.table("user_profiles").insert(profile).execute()
                    return profile
                except Exception:
                    # Return profile even if insert fails (RLS may prevent it)
                    return profile
        
        return None
        
    except Exception:
        # Fallback: return from session state if available
        return st.session_state.get("user_profile")


def update_user_profile(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user profile.
    
    Args:
        user_id: User UUID
        data: Dictionary with fields to update
        
    Returns:
        Dictionary with success status
    """
    if not SUPABASE_AVAILABLE:
        return {"success": False, "error": "Supabase not available."}
    
    sb = get_supabase_db()
    if not sb:
        return {"success": False, "error": "Failed to connect to Supabase."}
    
    try:
        # Update user profile
        data["updated_at"] = st.session_state.get("current_timestamp", "now()")
        response = sb.table("user_profiles").update(data).eq("id", user_id).execute()
        
        # Update session state
        if response.data:
            st.session_state.user_profile = response.data[0]
        
        return {
            "success": True,
            "message": "Profile updated successfully."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update profile: {str(e)}"
        }


def get_user_role(user_id: str) -> str:
    """
    Get user role.
    
    Args:
        user_id: User UUID
        
    Returns:
        User role (admin, scientist, viewer)
    """
    profile = get_user_profile(user_id)
    if profile:
        return profile.get("role", "scientist")
    return "scientist"


def set_user_role(user_id: str, role: str) -> Dict[str, Any]:
    """
    Set user role (admin only).
    
    Args:
        user_id: User UUID
        role: New role (admin, scientist, viewer)
        
    Returns:
        Dictionary with success status
    """
    # Check if current user is admin
    current_user = st.session_state.get("user_role", "scientist")
    if current_user != "admin":
        return {
            "success": False,
            "error": "Only administrators can change user roles."
        }
    
    return update_user_profile(user_id, {"role": role})


def get_user_company_id(user_id: str) -> Optional[str]:
    """
    Get user's company/organization ID.
    For multi-tenant isolation, we use organization name as company identifier.
    
    Args:
        user_id: User UUID
        
    Returns:
        Company/organization identifier or None
    """
    profile = get_user_profile(user_id)
    if profile:
        organization = profile.get("organization", "")
        if organization:
            # Use organization name as company identifier
            # In production, you might want a separate companies table with UUIDs
            return organization.lower().replace(" ", "_")
    return None


def get_user_organization(user_id: str) -> Optional[str]:
    """
    Get user's organization name.
    
    Args:
        user_id: User UUID
        
    Returns:
        Organization name or None
    """
    profile = get_user_profile(user_id)
    if profile:
        return profile.get("organization", "")
    return None

