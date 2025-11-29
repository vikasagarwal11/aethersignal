"""
PV Data Storage Module for AetherSignal
Handles persistent storage of pharmacovigilance data with multi-tenant isolation.
"""

import os
import pandas as pd
from typing import Optional, Dict, List, Any
import streamlit as st
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def get_supabase_db(use_service_key: bool = True) -> Optional[Client]:
    """
    Get Supabase client for database operations.
    
    Args:
        use_service_key: If True, use service key (bypasses RLS). If False, use anon key with user session.
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL", "https://scrksfxnkxmvvdzwmqnc.supabase.co")
    
    if use_service_key:
        # Use service key for backend operations (bypasses RLS)
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not key:
            # Development fallback - but this is anon key, not service key!
            key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY"
    else:
        # Use anon key and try to set user session if available
        key = os.getenv("SUPABASE_ANON_KEY")
        if not key:
            return None
    
    try:
        client = create_client(url, key)
        
        # If using anon key, try to set user session for RLS
        if not use_service_key:
            user_session = st.session_state.get("user_session")
            if user_session and hasattr(user_session, 'access_token'):
                try:
                    client.auth.set_session(user_session.access_token, user_session.refresh_token)
                except Exception:
                    pass  # Session might be expired
        
        return client
    except Exception:
        return None


def store_pv_data(df: pd.DataFrame, user_id: str, organization: str, source: str = "FAERS") -> Dict[str, Any]:
    """
    Store PV data in database with user/company association.
    
    Args:
        df: DataFrame with PV data
        user_id: User UUID
        organization: Company/organization name
        source: Data source (FAERS, E2B, Argus, etc.)
        
    Returns:
        Dictionary with success status and statistics
    """
    if not SUPABASE_AVAILABLE:
        return {
            "success": False,
            "error": "Supabase not available. Data not persisted."
        }
    
    if df.empty:
        return {
            "success": False,
            "error": "DataFrame is empty."
        }
    
    sb = get_supabase_db()
    if not sb:
        return {
            "success": False,
            "error": "Failed to connect to Supabase."
        }
    
    try:
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            record = {
                "user_id": user_id,
                "organization": organization,
                "source": source,
                "case_id": str(row.get("case_id", row.get("caseid", row.get("primaryid", "")))),
                "primaryid": str(row.get("primaryid", "")),
                "isr": str(row.get("isr", "")),
                "drug_name": str(row.get("drug_name", "")),
                "drug_count": int(row.get("drug_count", 0)) if pd.notna(row.get("drug_count")) else 0,
                "reaction": str(row.get("reaction", "")),
                "reaction_count": int(row.get("reaction_count", 0)) if pd.notna(row.get("reaction_count")) else 0,
                "age": float(row.get("age", 0)) if pd.notna(row.get("age")) else None,
                "age_yrs": float(row.get("age_yrs", 0)) if pd.notna(row.get("age_yrs")) else None,
                "sex": str(row.get("sex", "")),
                "gender": str(row.get("gender", "")),
                "country": str(row.get("country", "")),
                "serious": bool(row.get("serious", False)) if pd.notna(row.get("serious")) else None,
                "seriousness": str(row.get("seriousness", "")),
                "onset_date": str(row.get("onset_date", ""))[:10] if pd.notna(row.get("onset_date")) else None,  # Limit to date part
                "event_date": str(row.get("event_date", ""))[:10] if pd.notna(row.get("event_date")) else None,
                "report_date": str(row.get("report_date", ""))[:10] if pd.notna(row.get("report_date")) else None,
                "receive_date": str(row.get("receive_date", ""))[:10] if pd.notna(row.get("receive_date")) else None,
                "outcome": str(row.get("outcome", "")),
                "raw_data": row.to_dict()  # Store original row as JSON
            }
            records.append(record)
        
        # Insert in batches (Supabase has limits)
        batch_size = 1000
        total_inserted = 0
        errors = 0
        error_details = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(records) + batch_size - 1) // batch_size
            
            try:
                response = sb.table("pv_cases").insert(batch).execute()
                
                # Check if response has data (successful insert)
                if response.data and len(response.data) > 0:
                    total_inserted += len(response.data)
                else:
                    # No data returned - likely RLS blocked or silent failure
                    errors += len(batch)
                    error_details.append(f"Batch {batch_num}/{total_batches}: No data returned (possibly blocked by RLS)")
                    
            except Exception as e:
                errors += len(batch)
                error_msg = str(e)
                # Store first few error messages for debugging
                if len(error_details) < 5:
                    error_details.append(f"Batch {batch_num}/{total_batches}: {error_msg[:200]}")
                # Continue with next batch
        
        # If nothing was inserted, this is a failure
        if total_inserted == 0 and len(records) > 0:
            # Collect error information
            error_summary = "; ".join(error_details[:3]) if error_details else "Unknown error - check database connection and RLS policies"
            return {
                "success": False,
                "inserted": 0,
                "errors": errors,
                "total": len(records),
                "error": f"No records inserted. Possible causes: RLS policy blocking, invalid user_id, or database connection issue. Details: {error_summary}",
                "error_details": error_details[:5] if error_details else []
            }
        
        # Partial or full success
        success = errors == 0
        return {
            "success": success,
            "inserted": total_inserted,
            "errors": errors,
            "total": len(records),
            "message": f"Stored {total_inserted:,} cases in database." + (f" ({errors:,} failed)" if errors > 0 else ""),
            "error_details": error_details[:5] if error_details and errors > 0 else []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to store data: {str(e)}"
        }


def load_pv_data(user_id: str, organization: Optional[str] = None, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Load PV data from database for a specific user/company.
    
    Args:
        user_id: User UUID
        organization: Optional organization filter
        limit: Optional limit on number of records
        
    Returns:
        DataFrame with PV data or None
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    sb = get_supabase_db()
    if not sb:
        return None
    
    try:
        query = sb.table("pv_cases").select("*")
        
        # Filter by user_id (RLS should handle this, but we add it explicitly)
        query = query.eq("user_id", user_id)
        
        if organization:
            query = query.eq("organization", organization)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Remove internal fields that aren't part of original schema
            columns_to_drop = ['id', 'user_id', 'organization', 'created_at', 'updated_at', 'raw_data']
            for col in columns_to_drop:
                if col in df.columns:
                    df = df.drop(columns=[col])
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return None


def get_user_data_stats(user_id: str, organization: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about user's stored data.
    
    Args:
        user_id: User UUID
        organization: Optional organization filter
        
    Returns:
        Dictionary with statistics
    """
    if not SUPABASE_AVAILABLE:
        return {}
    
    sb = get_supabase_db()
    if not sb:
        return {}
    
    try:
        query = sb.table("pv_cases").select("id, drug_name, reaction, source", count="exact")
        query = query.eq("user_id", user_id)
        
        if organization:
            query = query.eq("organization", organization)
        
        response = query.execute()
        
        total_cases = response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
        
        # Get unique counts
        if response.data:
            df = pd.DataFrame(response.data)
            unique_drugs = df['drug_name'].nunique() if 'drug_name' in df.columns else 0
            unique_reactions = df['reaction'].nunique() if 'reaction' in df.columns else 0
            sources = df['source'].unique().tolist() if 'source' in df.columns else []
        else:
            unique_drugs = 0
            unique_reactions = 0
            sources = []
        
        return {
            "total_cases": total_cases,
            "unique_drugs": unique_drugs,
            "unique_reactions": unique_reactions,
            "sources": sources
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }


def delete_user_data(user_id: str, organization: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete all PV data for a user/company.
    
    Args:
        user_id: User UUID
        organization: Optional organization filter
        
    Returns:
        Dictionary with success status
    """
    if not SUPABASE_AVAILABLE:
        return {"success": False, "error": "Supabase not available."}
    
    sb = get_supabase_db()
    if not sb:
        return {"success": False, "error": "Failed to connect to Supabase."}
    
    try:
        query = sb.table("pv_cases").delete()
        query = query.eq("user_id", user_id)
        
        if organization:
            query = query.eq("organization", organization)
        
        response = query.execute()
        
        return {
            "success": True,
            "message": "Data deleted successfully."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete data: {str(e)}"
        }

