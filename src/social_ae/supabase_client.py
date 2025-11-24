"""
Simplified Supabase client for Social AE.
Uses service key for backend operations.
"""

import os
from typing import Optional

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase() -> Optional[Client]:
    """
    Get Supabase client with service key.
    
    For backend operations only. Never expose service key in frontend.
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL", "https://scrksfxnkxmvvdzwmqnc.supabase.co")
    
    # Use service key for backend, anon key for frontend
    # Service key bypasses RLS - use only in secure backend
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not key:
        # WARNING: Fallback key is for development only
        # In production, SUPABASE_SERVICE_KEY must be set via environment variable
        import warnings
        warnings.warn(
            "Supabase service key not found in environment. Using development fallback. "
            "Set SUPABASE_SERVICE_KEY environment variable for production use.",
            UserWarning
        )
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY"
    
    try:
        return create_client(url, key)
    except Exception:
        return None


def get_supabase_anon() -> Optional[Client]:
    """
    Get Supabase client with anon key (for frontend).
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL", "https://scrksfxnkxmvvdzwmqnc.supabase.co")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not key:
        # WARNING: Fallback key is for development only
        # In production, SUPABASE_ANON_KEY must be set via environment variable
        import warnings
        warnings.warn(
            "Supabase anon key not found in environment. Using development fallback. "
            "Set SUPABASE_ANON_KEY environment variable for production use.",
            UserWarning
        )
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY"
    
    try:
        return create_client(url, key)
    except Exception:
        return None

