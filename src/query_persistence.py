"""
Query Persistence Module for AetherSignal
Handles persistence of query history and saved queries to database.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase_db(use_service_key: bool = False):
    """Get Supabase client - reuse from pv_storage."""
    try:
        from src.pv_storage import get_supabase_db as _get_supabase_db
        return _get_supabase_db(use_service_key=use_service_key)
    except Exception:
        return None


def save_query_to_history(
    user_id: str,
    organization: str,
    query_text: str,
    filters: Optional[Dict] = None,
    source: str = "nl",
    results_count: Optional[int] = None,
    execution_time_ms: Optional[int] = None
) -> bool:
    """
    Save a query to query_history table.
    
    Args:
        user_id: User UUID
        organization: Organization name
        query_text: Query text
        filters: Optional filter dictionary
        source: Query source ('nl', 'form', etc.)
        results_count: Number of results
        execution_time_ms: Execution time in milliseconds
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=False)  # Use user session for RLS
    if not sb:
        return False
    
    try:
        record = {
            "user_id": user_id,
            "organization": organization,
            "query_text": query_text,
            "source": source,
            "created_at": datetime.now().isoformat()
        }
        
        if filters:
            record["filters"] = filters
        if results_count is not None:
            record["results_count"] = results_count
        if execution_time_ms is not None:
            record["execution_time_ms"] = execution_time_ms
        
        response = sb.table("query_history").insert(record).execute()
        
        return response.data is not None
    except Exception:
        # Silently fail - don't break query execution
        return False


def load_query_history(
    user_id: str,
    organization: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Load query history from database.
    
    Args:
        user_id: User UUID
        organization: Organization name
        limit: Maximum number of records
        
    Returns:
        List of query history records
    """
    if not SUPABASE_AVAILABLE:
        return []
    
    sb = get_supabase_db(use_service_key=False)
    if not sb:
        return []
    
    try:
        query = sb.table("query_history").select("*")
        query = query.eq("user_id", user_id)
        query = query.eq("organization", organization)
        query = query.order("created_at", desc=True)
        query = query.limit(limit)
        
        response = query.execute()
        
        if response.data:
            return response.data
        return []
    except Exception:
        return []


def save_query(
    user_id: str,
    organization: str,
    name: str,
    query_text: str,
    filters: Optional[Dict] = None,
    description: Optional[str] = None
) -> bool:
    """
    Save a query to saved_queries table.
    
    Args:
        user_id: User UUID
        organization: Organization name
        name: Query name
        query_text: Query text
        filters: Optional filter dictionary
        description: Optional description
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=False)
    if not sb:
        return False
    
    try:
        record = {
            "user_id": user_id,
            "organization": organization,
            "name": name,
            "query_text": query_text,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if filters:
            record["filters"] = filters
        if description:
            record["description"] = description
        
        # Check if query with same name already exists
        existing = sb.table("saved_queries").select("id").eq("user_id", user_id).eq("name", name).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing
            response = sb.table("saved_queries").update(record).eq("user_id", user_id).eq("name", name).execute()
        else:
            # Insert new
            response = sb.table("saved_queries").insert(record).execute()
        
        return response.data is not None
    except Exception:
        return False


def load_saved_queries(
    user_id: str,
    organization: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Load saved queries from database.
    
    Args:
        user_id: User UUID
        organization: Organization name
        limit: Maximum number of records
        
    Returns:
        List of saved query records
    """
    if not SUPABASE_AVAILABLE:
        return []
    
    sb = get_supabase_db(use_service_key=False)
    if not sb:
        return []
    
    try:
        query = sb.table("saved_queries").select("*")
        query = query.eq("user_id", user_id)
        query = query.eq("organization", organization)
        query = query.order("last_used_at", desc=True).nulls_last()
        query = query.order("created_at", desc=True)
        query = query.limit(limit)
        
        response = query.execute()
        
        if response.data:
            return response.data
        return []
    except Exception:
        return []


def update_saved_query_usage(
    user_id: str,
    query_name: str
) -> bool:
    """
    Update saved query usage count and last_used_at.
    
    Args:
        user_id: User UUID
        query_name: Query name
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=False)
    if not sb:
        return False
    
    try:
        # Get current usage_count
        existing = sb.table("saved_queries").select("usage_count").eq("user_id", user_id).eq("name", query_name).execute()
        
        current_count = 0
        if existing.data and len(existing.data) > 0:
            current_count = existing.data[0].get("usage_count", 0) or 0
        
        update_data = {
            "usage_count": current_count + 1,
            "last_used_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = sb.table("saved_queries").update(update_data).eq("user_id", user_id).eq("name", query_name).execute()
        
        return response.data is not None
    except Exception:
        return False


def delete_saved_query(
    user_id: str,
    query_name: str
) -> bool:
    """
    Delete a saved query.
    
    Args:
        user_id: User UUID
        query_name: Query name
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=False)
    if not sb:
        return False
    
    try:
        response = sb.table("saved_queries").delete().eq("user_id", user_id).eq("name", query_name).execute()
        return True
    except Exception:
        return False

