"""
Public Data Storage - Store AE data in public_ae_data table.
This is for the public data platform - no user_id or organization.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

from src.pv_storage import get_supabase_db

logger = logging.getLogger(__name__)


def store_public_ae_data(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Store AE data in public_ae_data table (public data platform).
    
    Args:
        records: List of normalized AE entries (from any source)
    
    Returns:
        Dictionary with insertion results
    """
    if not records:
        return {
            "success": True,
            "inserted": 0,
            "errors": 0,
            "message": "No records to store"
        }
    
    sb = get_supabase_db(use_service_key=True)  # Use service key for public data
    if not sb:
        logger.error("Supabase not available for public data storage")
        return {
            "success": False,
            "inserted": 0,
            "errors": len(records),
            "error": "Supabase not available"
        }
    
    try:
        # Prepare records for insertion
        prepared_records = []
        for record in records:
            try:
                # Normalize to public_ae_data schema
                prepared_record = {
                    "drug_name": str(record.get("drug", record.get("drug_name", ""))).lower().strip(),
                    "reaction": str(record.get("reaction", "")) if record.get("reaction") else None,
                    "source": str(record.get("source", "unknown")),
                    "text": str(record.get("text", ""))[:5000],  # Limit text length
                    "timestamp": record.get("timestamp") or datetime.now().isoformat(),
                    "confidence": float(record.get("confidence", 0.5)),
                    "severity": float(record.get("severity", 0.0)),
                    "metadata": record.get("metadata", {})
                }
                
                # Skip if no drug name
                if not prepared_record["drug_name"]:
                    continue
                
                # Convert timestamp to ISO string if needed
                if isinstance(prepared_record["timestamp"], datetime):
                    prepared_record["timestamp"] = prepared_record["timestamp"].isoformat()
                
                prepared_records.append(prepared_record)
            except Exception as e:
                logger.warning(f"Error preparing record: {str(e)}")
                continue
        
        if not prepared_records:
            return {
                "success": True,
                "inserted": 0,
                "errors": len(records),
                "message": "No valid records after preparation"
            }
        
        # Insert in batches (Supabase has limits)
        batch_size = 500
        total_inserted = 0
        total_errors = 0
        
        for i in range(0, len(prepared_records), batch_size):
            batch = prepared_records[i:i + batch_size]
            try:
                result = sb.table("public_ae_data").insert(batch).execute()
                inserted_count = len(result.data) if result.data else len(batch)
                total_inserted += inserted_count
                logger.info(f"Inserted {inserted_count} records into public_ae_data (batch {i//batch_size + 1})")
            except Exception as e:
                logger.error(f"Error inserting batch {i//batch_size + 1}: {str(e)}")
                total_errors += len(batch)
        
        return {
            "success": True,
            "inserted": total_inserted,
            "errors": total_errors,
            "total_records": len(records),
            "prepared_records": len(prepared_records)
        }
    
    except Exception as e:
        logger.error(f"Error storing public AE data: {str(e)}", exc_info=True)
        return {
            "success": False,
            "inserted": 0,
            "errors": len(records),
            "error": str(e)
        }


def store_from_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Store AE data from DataFrame to public_ae_data table.
    
    Args:
        df: DataFrame with normalized AE entries
    
    Returns:
        Dictionary with insertion results
    """
    if df.empty:
        return {
            "success": True,
            "inserted": 0,
            "errors": 0,
            "message": "DataFrame is empty"
        }
    
    # Convert DataFrame to list of dicts
    records = df.to_dict('records')
    return store_public_ae_data(records)

