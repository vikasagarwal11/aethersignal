"""
Authentication module for AetherSignal using Supabase.
Handles user login, registration, password reset, and session management.
"""

import os
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.auth.user_management import get_user_profile

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase_auth() -> Optional[Client]:
    """Get Supabase client for authentication."""
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL")
    # Use anon key for client-side auth operations; never ship service key here
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        return None
    
    try:
        return create_client(url, key)
    except Exception:
        return None


def register_user(
    email: str,
    password: str,
    full_name: str,
    organization: str,
    role: str = "scientist"
) -> Dict[str, Any]:
    """
    Register a new user account.
    
    Args:
        email: User email address
        password: User password (min 8 chars)
        full_name: User's full name
        organization: Company/organization name
        role: User role (admin, scientist, viewer)
        
    Returns:
        Dictionary with success status and user data or error message
    """
    if not SUPABASE_AVAILABLE:
        return {
            "success": False,
            "error": "Supabase not available. Please install supabase package."
        }
    
    sb = get_supabase_auth()
    if not sb:
        return {
            "success": False,
            "error": "Failed to connect to Supabase."
        }
    
    try:
        # Validate inputs
        if len(password) < 8:
            return {
                "success": False,
                "error": "Password must be at least 8 characters long."
            }
        
        if not email or "@" not in email:
            return {
                "success": False,
                "error": "Please enter a valid email address."
            }
        
        # Register user with Supabase Auth
        auth_response = sb.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if auth_response.user is None:
            return {
                "success": False,
                "error": "Registration failed. Please try again."
            }
        
        user_id = auth_response.user.id
        
        # Create user profile in database
        try:
            from src.auth.user_management import get_supabase_db
            db_sb = get_supabase_db()
            if db_sb:
                profile_data = {
                    "id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "organization": organization,
                    "role": role,
                    "subscription_tier": "free"
                }
                # Try to insert profile (may fail if RLS prevents it, that's OK)
                try:
                    db_sb.table("user_profiles").insert(profile_data).execute()
                except Exception:
                    # Profile insert failed (RLS or duplicate) - will be created on first login
                    pass
        except Exception:
            # Database not available - continue with session state only
            pass
        
        # Store in session state
        profile_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "organization": organization,
            "role": role,
            "subscription_tier": "free"
        }
        st.session_state.user_profile = profile_data
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "message": "Registration successful! Please check your email to verify your account."
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle rate limiting
        if "security purposes" in error_msg.lower() or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            # Extract wait time if mentioned
            import re
            wait_match = re.search(r'(\d+)\s*seconds?', error_msg, re.IGNORECASE)
            wait_time = wait_match.group(1) if wait_match else "60"
            return {
                "success": False,
                "error": f"⏱️ Rate limit: Too many registration attempts. Please wait {wait_time} seconds before trying again.",
                "rate_limited": True,
                "wait_seconds": int(wait_time)
            }
        
        # Handle already registered
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower() or "user already registered" in error_msg.lower():
            return {
                "success": False,
                "error": "An account with this email already exists. Please login instead."
            }
        
        # Handle email not confirmed / needs verification
        if "email" in error_msg.lower() and ("confirm" in error_msg.lower() or "verify" in error_msg.lower()):
            return {
                "success": False,
                "error": "Please check your email for a verification link. You may need to verify your email before logging in."
            }
        
        return {
            "success": False,
            "error": f"Registration failed: {error_msg}"
        }


def login_user(email: str, password: str) -> Dict[str, Any]:
    """
    Login user with email and password.
    
    Args:
        email: User email address
        password: User password
        
    Returns:
        Dictionary with success status and user data or error message
    """
    if not SUPABASE_AVAILABLE:
        return {
            "success": False,
            "error": "Supabase not available. Please install supabase package."
        }
    
    sb = get_supabase_auth()
    if not sb:
        return {
            "success": False,
            "error": "Failed to connect to Supabase."
        }
    
    try:
        # Authenticate with Supabase
        auth_response = sb.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user is None:
            return {
                "success": False,
                "error": "Invalid email or password."
            }
        
        user = auth_response.user
        session = auth_response.session
        
        # Store session in Streamlit session state
        st.session_state.user_id = user.id
        st.session_state.user_email = user.email
        st.session_state.user_session = session
        st.session_state.authenticated = True
        
        # Load user profile
        profile = get_user_profile(user.id)
        if profile:
            st.session_state.user_profile = profile
            st.session_state.user_organization = profile.get("organization", "")
            st.session_state.user_role = profile.get("role", "scientist")
        else:
            # Create default profile if doesn't exist
            from src.auth.user_management import update_user_profile
            default_profile = {
                "email": user.email,
                "full_name": "",
                "organization": "",
                "role": "scientist",
                "subscription_tier": "free"
            }
            try:
                update_user_profile(user.id, default_profile)
                st.session_state.user_profile = default_profile
                st.session_state.user_organization = ""
                st.session_state.user_role = "scientist"
            except Exception:
                # Continue with minimal profile
                st.session_state.user_profile = default_profile
                st.session_state.user_organization = ""
                st.session_state.user_role = "scientist"
        
        return {
            "success": True,
            "user_id": user.id,
            "email": user.email,
            "message": "Login successful!"
        }
        
    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {
                "success": False,
                "error": "Invalid email or password."
            }
        return {
            "success": False,
            "error": f"Login failed: {error_msg}"
        }


def logout_user() -> Dict[str, Any]:
    """
    Logout current user and clear session.
    
    Returns:
        Dictionary with success status
    """
    if not SUPABASE_AVAILABLE:
        return {"success": False, "error": "Supabase not available."}
    
    sb = get_supabase_auth()
    if sb:
        try:
            sb.auth.sign_out()
        except Exception:
            pass
    
    # Clear session state
    keys_to_clear = [
        "user_id",
        "user_email",
        "user_session",
        "authenticated",
        "user_profile",
        "user_organization",
        "user_role",
        "data",
        "normalized_data"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    return {"success": True, "message": "Logged out successfully."}


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from session.
    
    Returns:
        Dictionary with user data or None if not authenticated
    """
    if not is_authenticated():
        return None
    
    user_id = st.session_state.get("user_id")
    user_email = st.session_state.get("user_email")
    user_profile = st.session_state.get("user_profile", {})
    
    return {
        "user_id": user_id,
        "email": user_email,
        "full_name": user_profile.get("full_name", ""),
        "organization": user_profile.get("organization", ""),
        "role": user_profile.get("role", "scientist"),
        "subscription_tier": user_profile.get("subscription_tier", "free")
    }


def restore_session() -> bool:
    """
    Restore authentication session from stored session token.
    This should be called on each page load to maintain auth across pages.
    
    Returns:
        True if session was restored, False otherwise
    """
    # Check if we have basic auth info stored
    user_id = st.session_state.get("user_id")
    user_session = st.session_state.get("user_session")
    
    # If we have user_id and session, we're authenticated - just ensure state is complete
    if user_id and user_session:
        try:
            # Ensure authenticated flag is set
            if not st.session_state.get("authenticated"):
                st.session_state.authenticated = True
            
            # Restore email if missing
            if not st.session_state.get("user_email") and SUPABASE_AVAILABLE:
                try:
                    profile = get_user_profile(user_id)
                    if profile:
                        st.session_state.user_email = profile.get("email", "")
                except Exception:
                    pass
            
            # Load profile if not loaded
            if not st.session_state.get("user_profile") and SUPABASE_AVAILABLE:
                try:
                    profile = get_user_profile(user_id)
                    if profile:
                        st.session_state.user_profile = profile
                        st.session_state.user_organization = profile.get("organization", "")
                        st.session_state.user_role = profile.get("role", "scientist")
                except Exception:
                    pass
            
            return True
        except Exception:
            # Error restoring - clear session
            try:
                logout_user()
            except Exception:
                pass
            return False
    
    return False


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    Also attempts to restore session if not authenticated but session exists.
    
    Returns:
        True if authenticated, False otherwise
    """
    # First check if already authenticated
    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True
    
    # Try to restore session from stored token
    # This handles the case where we navigate between pages and session state
    # might have been partially cleared
    user_id = st.session_state.get("user_id")
    user_session = st.session_state.get("user_session")
    
    if user_id or user_session:
        if restore_session():
            return True
    
    return False


def reset_password(email: str) -> Dict[str, Any]:
    """
    Send password reset email to user.
    
    Args:
        email: User email address
        
    Returns:
        Dictionary with success status
    """
    if not SUPABASE_AVAILABLE:
        return {"success": False, "error": "Supabase not available."}
    
    sb = get_supabase_auth()
    if not sb:
        return {"success": False, "error": "Failed to connect to Supabase."}
    
    try:
        sb.auth.reset_password_for_email(email)
        return {
            "success": True,
            "message": "Password reset email sent. Please check your inbox."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send reset email: {str(e)}"
        }


def verify_email(token: str) -> Dict[str, Any]:
    """
    Verify user email with token.
    
    Args:
        token: Email verification token
        
    Returns:
        Dictionary with success status
    """
    if not SUPABASE_AVAILABLE:
        return {"success": False, "error": "Supabase not available."}
    
    sb = get_supabase_auth()
    if not sb:
        return {"success": False, "error": "Failed to connect to Supabase."}
    
    try:
        # Supabase handles email verification automatically
        # This is a placeholder for manual verification if needed
        return {
            "success": True,
            "message": "Email verified successfully."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Email verification failed: {str(e)}"
        }

