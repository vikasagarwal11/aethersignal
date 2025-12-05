"""
File Upload History Module for AetherSignal
Handles file upload tracking, duplicate detection, and metadata storage.
"""

import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase_db(use_service_key: bool = True):
    """Get Supabase client - reuse from pv_storage to avoid duplication."""
    try:
        from src.pv_storage import get_supabase_db as _get_supabase_db
        return _get_supabase_db(use_service_key=use_service_key)
    except Exception:
        return None


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate MD5 hash of file content for duplicate detection."""
    return hashlib.md5(file_content).hexdigest()


def check_duplicate_file(
    user_id: str,
    organization: str,
    filename: str,
    file_size_bytes: int,
    file_hash: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if file with same filename + size was uploaded before.
    
    Args:
        user_id: User UUID
        organization: Organization name
        filename: File name
        file_size_bytes: File size in bytes
        file_hash: Optional MD5 hash for stronger duplicate detection
        
    Returns:
        Dictionary with duplicate file info if found, None otherwise
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    sb = get_supabase_db(use_service_key=True)
    if not sb:
        return None
    
    try:
        query = sb.table("file_upload_history").select("*")
        query = query.eq("user_id", user_id)
        query = query.eq("organization", organization)
        query = query.eq("filename", filename)
        query = query.eq("file_size_bytes", file_size_bytes)
        query = query.order("uploaded_at", desc=True)
        query = query.limit(1)
        
        response = query.execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


def create_file_upload_record(
    user_id: str,
    organization: str,
    filename: str,
    file_size_bytes: int,
    file_type: str = "FAERS",
    source: str = "FAERS",
    file_hash: Optional[str] = None
) -> Optional[str]:
    """
    Create file upload history record.
    Returns upload_id immediately (before processing).
    
    Args:
        user_id: User UUID
        organization: Organization name
        filename: File name
        file_size_bytes: File size in bytes
        file_type: File type ('FAERS', 'E2B', 'CSV', 'Excel', etc.)
        source: Data source ('FAERS', 'E2B', etc.)
        file_hash: Optional MD5 hash
        
    Returns:
        Upload ID (UUID) if successful, None otherwise
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    sb = get_supabase_db(use_service_key=True)
    if not sb:
        return None
    
    try:
        record = {
            "user_id": user_id,
            "organization": organization,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "file_hash_md5": file_hash,
            "file_type": file_type,
            "source": source,
            "upload_status": "processing",
            "stats_status": "pending",
            "processing_started_at": datetime.now().isoformat()
        }
        
        response = sb.table("file_upload_history").insert(record).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        return None


def update_file_upload_status(
    upload_id: str,
    status: str = "completed",
    total_cases: Optional[int] = None,
    error: Optional[str] = None
) -> bool:
    """
    Update file upload history record with processing status.
    
    Args:
        upload_id: Upload record ID
        status: Status ('processing', 'completed', 'failed')
        total_cases: Total number of cases (if completed)
        error: Error message (if failed)
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=True)
    if not sb:
        return False
    
    try:
        update_data = {
            "upload_status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if status == "completed":
            update_data["processing_completed_at"] = datetime.now().isoformat()
            if total_cases is not None:
                update_data["total_cases"] = total_cases
        elif status == "failed":
            update_data["processing_completed_at"] = datetime.now().isoformat()
            if error:
                update_data["processing_error"] = error
        
        response = sb.table("file_upload_history").update(update_data).eq("id", upload_id).execute()
        
        return response.data is not None
    except Exception:
        return False


def update_file_upload_stats(
    upload_id: str,
    total_cases: int,
    total_events: int,
    total_drugs: int,
    total_serious_cases: int,
    total_fatal_cases: int,
    earliest_date: Optional[str] = None,
    latest_date: Optional[str] = None
) -> bool:
    """
    Update file upload history with calculated statistics.
    
    Args:
        upload_id: Upload record ID
        total_cases: Total number of cases
        total_events: Number of unique reactions/events
        total_drugs: Number of unique drugs
        total_serious_cases: Number of serious cases
        total_fatal_cases: Number of fatal cases
        earliest_date: Earliest case date (ISO format)
        latest_date: Latest case date (ISO format)
        
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        return False
    
    sb = get_supabase_db(use_service_key=True)
    if not sb:
        return False
    
    try:
        update_data = {
            "total_cases": total_cases,
            "total_events": total_events,
            "total_drugs": total_drugs,
            "total_serious_cases": total_serious_cases,
            "total_fatal_cases": total_fatal_cases,
            "stats_status": "completed",
            "stats_calculated_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if earliest_date:
            update_data["earliest_date"] = earliest_date
        if latest_date:
            update_data["latest_date"] = latest_date
        
        response = sb.table("file_upload_history").update(update_data).eq("id", upload_id).execute()
        
        return response.data is not None
    except Exception:
        return False


def list_file_uploads(
    user_id: str,
    organization: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List file uploads for a user/organization.
    
    Args:
        user_id: User UUID
        organization: Organization name
        limit: Maximum number of records to return
        
    Returns:
        List of file upload records
    """
    if not SUPABASE_AVAILABLE:
        return []
    
    sb = get_supabase_db(use_service_key=True)
    if not sb:
        return []
    
    try:
        query = sb.table("file_upload_history").select("*")
        query = query.eq("user_id", user_id)
        query = query.eq("organization", organization)
        query = query.order("uploaded_at", desc=True)
        query = query.limit(limit)
        
        response = query.execute()
        
        if response.data:
            return response.data
        return []
    except Exception:
        return []

