"""
Simplified storage layer for Social AE.
Uses Supabase with simplified schema.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .supabase_client import get_supabase


def store_social_records(df: pd.DataFrame) -> Dict:
    """
    Store Social AE records in Supabase.
    
    Args:
        df: DataFrame with columns matching Supabase schema
    
    Returns:
        Dictionary with insertion results
    """
    if df.empty:
        return {"inserted": 0, "errors": 0}
    
    sb = get_supabase()
    if not sb:
        return {"inserted": 0, "errors": len(df), "error": "Supabase not available"}
    
    # Prepare records - map to simplified schema
    records = []
    for _, row in df.iterrows():
        try:
            record = {
                "source": row.get("platform", row.get("source", "reddit")),
                "drug_name": row.get("drug_match", row.get("drug_name", "")),
                "reaction": row.get("reaction"),
                "meddra_pt": row.get("meddra_pt"),
                "ae_prob": float(row.get("ae_prob", row.get("confidence_score", 0.0))),
                "created": row.get("created_date") or (
                    datetime.fromtimestamp(row.get("created_utc", 0)) if row.get("created_utc") else datetime.now()
                ),
                "text": row.get("cleaned_text", row.get("text", "")),
                "subreddit": row.get("subreddit", ""),
                "score": int(row.get("score", 0)),
            }
            
            # Convert datetime to ISO string if needed
            if isinstance(record["created"], datetime):
                record["created"] = record["created"].isoformat()
            
            records.append(record)
        except Exception:
            continue
    
    if not records:
        return {"inserted": 0, "errors": len(df)}
    
    # Insert in batches
    batch_size = 500
    inserted = 0
    errors = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            # Insert batch - Supabase will handle duplicates if unique constraint exists
            result = sb.table("social_ae").insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            # If duplicate error, try individual inserts to skip duplicates
            if "duplicate" in str(e).lower() or "unique" in str(e).lower() or "violates unique" in str(e).lower():
                # Insert one by one to handle duplicates gracefully
                for record in batch:
                    try:
                        sb.table("social_ae").insert(record).execute()
                        inserted += 1
                    except Exception:
                        errors += 1
            else:
                errors += len(batch)
                continue
    
    return {
        "inserted": inserted,
        "errors": errors,
        "total": len(records)
    }


def load_recent_social(days: int = 30) -> pd.DataFrame:
    """
    Load recent Social AE records from Supabase.
    
    Args:
        days: Number of days back to load
    
    Returns:
        DataFrame with Social AE records
    """
    sb = get_supabase()
    if not sb:
        return pd.DataFrame()
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = sb.table("social_ae").select("*").gte(
            "created", cutoff_date
        ).order("created", desc=True).limit(10000).execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def get_social_statistics() -> Dict:
    """Get statistics from Social AE table."""
    sb = get_supabase()
    if not sb:
        return {}
    
    try:
        # Total count
        total_response = sb.table("social_ae").select("id", count="exact").execute()
        total = total_response.count or 0
        
        # Recent count (last 7 days)
        recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        recent_response = sb.table("social_ae").select("id", count="exact").gte(
            "created", recent_cutoff
        ).execute()
        recent = recent_response.count or 0
        
        return {
            "total_posts": total,
            "recent_posts_7d": recent,
        }
    except Exception:
        return {}

