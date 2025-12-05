"""
PV Data Storage Module for AetherSignal
Handles persistent storage of pharmacovigilance data with multi-tenant isolation.
"""

import os
import pandas as pd
from typing import Optional, Dict, List, Any
import streamlit as st
from datetime import datetime
import math
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def _clean_for_json(obj: Any) -> Any:
    """
    Recursively clean dict/list to remove NaN and Inf values for JSON compliance.
    
    Args:
        obj: Object to clean (dict, list, or primitive)
        
    Returns:
        Cleaned object with NaN/Inf replaced by None
    """
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None  # Convert NaN/Inf to None (JSON-compliant)
        return obj
    elif pd.isna(obj):
        return None
    else:
        return obj


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


def store_pv_data(df: pd.DataFrame, user_id: str, organization: str, source: str = "FAERS", skip_duplicate_check: bool = False) -> Dict[str, Any]:
    """
    Store PV data in database with user/company association.
    
    Args:
        df: DataFrame with PV data
        user_id: User UUID
        organization: Company/organization name
        source: Data source (FAERS, E2B, Argus, etc.)
        skip_duplicate_check: If True, save all records including duplicates (Option 3: Save All)
        
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
        # STEP 1: Check for duplicates (skip if Option 3: Save All is enabled)
        existing_case_ids = set()
        duplicates_skipped = 0
        
        if not skip_duplicate_check:
            # Extract case_ids from the DataFrame we're about to insert
            case_ids_to_check = set()
            
            for _, row in df.iterrows():
                case_id = str(row.get("case_id", row.get("caseid", row.get("primaryid", ""))))
                if case_id:  # Only check non-empty case_ids
                    case_ids_to_check.add(case_id)
            
            # Check which case_ids already exist in database
            if case_ids_to_check:
                try:
                    # Check existing case_ids in batches (Supabase query limit)
                    check_batch_size = 1000
                    case_ids_list = list(case_ids_to_check)
                    
                    for i in range(0, len(case_ids_list), check_batch_size):
                        batch_case_ids = case_ids_list[i:i + check_batch_size]
                        
                        # Query for existing case_ids matching this batch
                        existing_query = sb.table("pv_cases").select("case_id").eq("user_id", user_id).eq("organization", organization).in_("case_id", batch_case_ids)
                        
                        existing_response = existing_query.execute()
                        
                        if existing_response.data:
                            batch_existing = {str(rec.get("case_id", "")) for rec in existing_response.data if rec.get("case_id")}
                            existing_case_ids.update(batch_existing)
                except Exception as e:
                    # If query fails, proceed without duplicate check (safer to insert than to fail entirely)
                    # Log error but continue
                    pass
        
        # STEP 2: Prepare records for insertion
        records = []
        
        for _, row in df.iterrows():
            case_id = str(row.get("case_id", row.get("caseid", row.get("primaryid", ""))))
            
            # Skip duplicates only if duplicate check is enabled
            if not skip_duplicate_check:
                if case_id and case_id in existing_case_ids:
                    duplicates_skipped += 1
                    continue
            
            record = {
                "user_id": user_id,
                "organization": organization,
                "source": source,
                "case_id": case_id,
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
                "raw_data": _clean_for_json(row.to_dict())  # Store original row as JSON (NaN cleaned)
            }
            records.append(record)
        
        # If all records are duplicates, return early
        if not records:
            return {
                "success": True,
                "inserted": 0,
                "duplicates": duplicates_skipped,
                "total": len(df),
                "message": f"All {duplicates_skipped:,} cases already exist in database. No new records inserted."
            }
        
        # STEP 3: Insert only new records in batches
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
        message_parts = []
        if total_inserted > 0:
            message_parts.append(f"Stored {total_inserted:,} new case(s)")
        if duplicates_skipped > 0:
            message_parts.append(f"skipped {duplicates_skipped:,} duplicate(s)")
        if errors > 0:
            message_parts.append(f"{errors:,} failed")
        
        message = ". ".join(message_parts) + "."
        
        return {
            "success": success,
            "inserted": total_inserted,
            "duplicates": duplicates_skipped,
            "errors": errors,
            "total": len(df),
            "message": message,
            "error_details": error_details[:5] if error_details and errors > 0 else []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to store data: {str(e)}"
        }


def load_pv_data(
    user_id: str, 
    organization: Optional[str] = None, 
    limit: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    source: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Load PV data from database for a specific user/company.
    
    Args:
        user_id: User UUID
        organization: Optional organization filter
        limit: Optional limit on number of records (if None, loads all records with pagination)
        date_from: Optional filter by upload date (from)
        date_to: Optional filter by upload date (to)
        source: Optional filter by data source (FAERS, E2B, etc.)
        
    Returns:
        DataFrame with PV data or None
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    sb = get_supabase_db()
    if not sb:
        return None
    
    try:
        # Build base query
        query = sb.table("pv_cases").select("*")
        
        # Filter by user_id (RLS should handle this, but we add it explicitly)
        query = query.eq("user_id", user_id)
        
        if organization:
            query = query.eq("organization", organization)
        
        # Filter by upload date range (created_at)
        if date_from:
            query = query.gte("created_at", date_from.isoformat())
        if date_to:
            query = query.lte("created_at", date_to.isoformat())
        
        # Filter by source
        if source:
            query = query.eq("source", source)
        
        # If limit is specified, use it directly
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
        else:
            # No limit specified - use pagination to load ALL records
            # Supabase default limit is 1000, so we need to paginate
            all_data = []
            page_size = 1000
            offset = 0
            
            while True:
                # Build a fresh query for each page to avoid parameter accumulation
                page_query = sb.table("pv_cases").select("*")
                page_query = page_query.eq("user_id", user_id)
                
                if organization:
                    page_query = page_query.eq("organization", organization)
                
                # Filter by upload date range (created_at)
                if date_from:
                    page_query = page_query.gte("created_at", date_from.isoformat())
                if date_to:
                    page_query = page_query.lte("created_at", date_to.isoformat())
                
                # Filter by source
                if source:
                    page_query = page_query.eq("source", source)
                
                # Apply range for this page
                page_query = page_query.range(offset, offset + page_size - 1)
                
                response = page_query.execute()
                
                if not response.data or len(response.data) == 0:
                    break
                
                all_data.extend(response.data)
                
                # If we got fewer records than page_size, we've reached the end
                if len(response.data) < page_size:
                    break
                
                offset += page_size
            
            if all_data:
                df = pd.DataFrame(all_data)
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


def list_available_datasets(user_id: str, organization: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available datasets grouped by upload date/source.
    Helps users identify which datasets they have uploaded.
    
    Args:
        user_id: User UUID
        organization: Optional organization filter
        
    Returns:
        List of dictionaries with dataset info (date, source, count, etc.)
    """
    if not SUPABASE_AVAILABLE:
        return []
    
    sb = get_supabase_db()
    if not sb:
        return []
    
    try:
        # Get all records with created_at to group by upload date
        # Use pagination to get ALL records (not just first 1000)
        query = sb.table("pv_cases").select("created_at, source")
        query = query.eq("user_id", user_id)
        
        if organization:
            query = query.eq("organization", organization)
        
        # Order by created_at descending (newest first)
        query = query.order("created_at", desc=True)
        
        # OPTIMIZED: Sample records to identify datasets (don't need all records)
        # Strategy: Get records from different time periods to identify all unique date/source combinations
        # Maximum 10,000 records should be enough to identify all datasets
        
        all_data = []
        page_size = 1000
        max_records_to_sample = 10000  # Enough to identify all unique date/source combinations
        offset = 0
        
        while len(all_data) < max_records_to_sample:
            # Build a fresh query for each page to avoid parameter accumulation
            page_query = sb.table("pv_cases").select("created_at, source")
            page_query = page_query.eq("user_id", user_id)
            
            if organization:
                page_query = page_query.eq("organization", organization)
            
            # Order by created_at descending (newest first)
            page_query = page_query.order("created_at", desc=True)
            
            # Apply range for this page
            page_query = page_query.range(offset, offset + page_size - 1)
            
            response = page_query.execute()
            
            if not response.data or len(response.data) == 0:
                break
            
            all_data.extend(response.data)
            
            # If we got fewer records than page_size, we've reached the end
            if len(response.data) < page_size:
                break
            
            offset += page_size
        
        # Also get count for each dataset using aggregation (if possible)
        # Fallback: Use sampled data which should have all unique combinations
        
        if not all_data:
            return []
        
        df = pd.DataFrame(all_data)
        
        # Convert created_at to datetime
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df = df.dropna(subset=['created_at'])
        
        if df.empty:
            return []
        
        # Group by date (day) and source
        df['upload_date'] = df['created_at'].dt.date
        df['upload_datetime'] = df['created_at']
        
        # Get unique combinations of date and source from sampled data
        grouped = df.groupby(['upload_date', 'source']).agg({
            'created_at': ['count', 'min', 'max']
        }).reset_index()
        
        grouped.columns = ['upload_date', 'source', 'sampled_count', 'first_record', 'last_record']
        
        # Get accurate counts for each dataset using count queries
        datasets = []
        for _, row in grouped.iterrows():
            upload_date = row['upload_date']
            source = row['source']
            
            # Get accurate count for this dataset
            from datetime import datetime
            date_from = datetime.combine(upload_date, datetime.min.time())
            date_to = datetime.combine(upload_date, datetime.max.time())
            
            count_query = sb.table("pv_cases").select("id", count="exact")
            count_query = count_query.eq("user_id", user_id)
            if organization:
                count_query = count_query.eq("organization", organization)
            count_query = count_query.gte("created_at", date_from.isoformat())
            count_query = count_query.lte("created_at", date_to.isoformat())
            count_query = count_query.eq("source", source)
            
            try:
                count_response = count_query.execute()
                case_count = count_response.count if hasattr(count_response, 'count') else row['sampled_count']
            except Exception:
                # Fallback to sampled count if count query fails
                case_count = row['sampled_count']
            
            datasets.append({
                'upload_date': upload_date,
                'source': source,
                'case_count': int(case_count),
                'first_record': row['first_record'].isoformat() if pd.notna(row['first_record']) else None,
                'last_record': row['last_record'].isoformat() if pd.notna(row['last_record']) else None,
                'date_label': upload_date.strftime('%Y-%m-%d') if pd.notna(upload_date) else 'Unknown'
            })
        
        # Sort by date descending (newest first)
        datasets.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return datasets
        
    except Exception as e:
        return []


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

