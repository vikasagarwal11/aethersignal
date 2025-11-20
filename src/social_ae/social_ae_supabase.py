"""
Supabase storage module for Social AE posts.
Handles persistence, deduplication, and historical tracking in Supabase.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scrksfxnkxmvvdzwmqnc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY")

# Table name
TABLE_NAME = "social_ae"


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client."""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def init_supabase_table():
    """Initialize Supabase table (run once via SQL editor)."""
    # SQL to run in Supabase SQL Editor:
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id BIGSERIAL PRIMARY KEY,
        platform TEXT NOT NULL,
        post_id TEXT NOT NULL,
        post_url TEXT,
        raw_text TEXT NOT NULL,
        cleaned_text TEXT,
        created_utc BIGINT,
        created_date TIMESTAMP,
        drug_name TEXT,
        drug_match TEXT,
        reaction TEXT,
        meddra_pt TEXT,
        meddra_pt_code TEXT,
        confidence_score REAL,
        ae_prob REAL,
        subreddit TEXT,
        author_hash TEXT,
        score INTEGER,
        is_anonymized BOOLEAN DEFAULT FALSE,
        source_context TEXT,
        engagement_score INTEGER,
        seriousness BOOLEAN DEFAULT FALSE,
        outcome TEXT,
        report_date TIMESTAMP,
        inserted_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(platform, post_id)
    );

    CREATE INDEX IF NOT EXISTS idx_drug_name ON {TABLE_NAME}(drug_name);
    CREATE INDEX IF NOT EXISTS idx_reaction ON {TABLE_NAME}(reaction);
    CREATE INDEX IF NOT EXISTS idx_created_utc ON {TABLE_NAME}(created_utc);
    CREATE INDEX IF NOT EXISTS idx_created_date ON {TABLE_NAME}(created_date);
    CREATE INDEX IF NOT EXISTS idx_platform_post_id ON {TABLE_NAME}(platform, post_id);
    """
    return sql


def store_posts_supabase(posts: List[Dict], drug_terms: str, platforms: List[str]) -> Dict:
    """
    Store posts in Supabase with deduplication.
    
    Args:
        posts: List of post dictionaries
        drug_terms: Comma-separated drug terms
        platforms: List of platforms used
    
    Returns:
        Dictionary with storage statistics
    """
    if not posts:
        return {"stored": 0, "duplicates": 0, "errors": 0}
    
    client = get_supabase_client()
    if not client:
        return {"stored": 0, "duplicates": 0, "errors": len(posts), "error": "Supabase not available"}
    
    stored = 0
    duplicates = 0
    errors = 0
    
    # Prepare records for insertion
    records = []
    for post in posts:
        try:
            # Normalize to FAERS-like structure
            created_utc = post.get("created_utc")
            created_date = post.get("created_date")
            
            if created_date and isinstance(created_date, datetime):
                created_date = created_date.isoformat()
            elif created_utc:
                try:
                    created_date = datetime.fromtimestamp(created_utc).isoformat()
                except (ValueError, OSError):
                    created_date = None
            
            record = {
                "platform": post.get("platform", post.get("source", "unknown")),
                "post_id": str(post.get("post_id", "")),
                "post_url": post.get("url", ""),
                "raw_text": post.get("text", post.get("raw_text", "")),
                "cleaned_text": post.get("cleaned_text", post.get("text", "")),
                "created_utc": created_utc,
                "created_date": created_date,
                "drug_name": post.get("drug_match", ""),  # For FAERS compatibility
                "drug_match": post.get("drug_match", ""),
                "reaction": post.get("reaction"),
                "meddra_pt": post.get("meddra_pt"),
                "meddra_pt_code": post.get("meddra_pt_code"),
                "confidence_score": post.get("confidence_score"),
                "ae_prob": post.get("ae_prob"),
                "subreddit": post.get("subreddit", ""),
                "author_hash": post.get("author_hash", post.get("author", "")),
                "score": post.get("score", 0),
                "is_anonymized": post.get("is_anonymized", False),
                "source_context": post.get("subreddit", ""),  # For FAERS compatibility
                "engagement_score": post.get("score", 0),  # For FAERS compatibility
                "seriousness": False,  # Social AE is always non-serious (observational)
                "outcome": None,
                "report_date": created_date,  # For FAERS compatibility
            }
            
            records.append(record)
        except Exception:
            errors += 1
            continue
    
    # Insert in batches (Supabase has limits)
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            # Use upsert to handle duplicates
            result = client.table(TABLE_NAME).upsert(
                batch,
                on_conflict="platform,post_id"
            ).execute()
            
            # Count new vs duplicates (approximate)
            stored += len(batch)
        except Exception as e:
            errors += len(batch)
            continue
    
    # Log pull history (optional - can create separate table)
    try:
        client.table("pull_history").insert({
            "drug_terms": drug_terms,
            "platforms": ",".join(platforms),
            "posts_fetched": len(posts),
            "posts_new": stored,
            "posts_duplicate": duplicates,
            "status": "success" if errors == 0 else f"partial ({errors} errors)"
        }).execute()
    except Exception:
        pass  # Ignore if table doesn't exist
    
    return {
        "stored": stored,
        "duplicates": duplicates,
        "errors": errors,
        "total": len(posts)
    }


def get_posts_supabase(
    drug_name: Optional[str] = None,
    reaction: Optional[str] = None,
    platform: Optional[str] = None,
    days_back: Optional[int] = None,
    min_confidence: Optional[float] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Retrieve posts from Supabase with filters.
    
    Args:
        drug_name: Filter by drug name
        reaction: Filter by reaction
        platform: Filter by platform
        days_back: Get posts from last N days
        min_confidence: Minimum confidence score
        limit: Maximum number of posts to return
    
    Returns:
        DataFrame with posts
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    query = client.table(TABLE_NAME).select("*")
    
    if drug_name:
        query = query.ilike("drug_name", f"%{drug_name}%")
    
    if reaction:
        query = query.eq("reaction", reaction)
    
    if platform:
        query = query.eq("platform", platform)
    
    if days_back:
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        query = query.gte("created_date", cutoff_date)
    
    if min_confidence is not None:
        query = query.gte("confidence_score", min_confidence)
    
    query = query.order("created_utc", desc=True).limit(limit)
    
    try:
        result = query.execute()
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_statistics_supabase() -> Dict:
    """Get database statistics from Supabase."""
    client = get_supabase_client()
    if not client:
        return {}
    
    stats = {}
    
    try:
        # Total posts
        result = client.table(TABLE_NAME).select("id", count="exact").execute()
        stats["total_posts"] = result.count or 0
        
        # Posts by platform
        result = client.table(TABLE_NAME).select("platform").execute()
        if result.data:
            df = pd.DataFrame(result.data)
            stats["by_platform"] = df["platform"].value_counts().to_dict()
        
        # Posts with reactions
        result = client.table(TABLE_NAME).select("id", count="exact").not_.is_("reaction", "null").execute()
        stats["with_reactions"] = result.count or 0
        
        # Unique drugs
        result = client.table(TABLE_NAME).select("drug_name").execute()
        if result.data:
            df = pd.DataFrame(result.data)
            stats["unique_drugs"] = df["drug_name"].nunique()
        
        # Unique reactions
        result = client.table(TABLE_NAME).select("reaction").execute()
        if result.data:
            df = pd.DataFrame(result.data)
            stats["unique_reactions"] = df["reaction"].nunique()
        
    except Exception:
        pass
    
    return stats


def normalize_social_ae_to_faers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Social AE DataFrame to FAERS-like structure for integration.
    
    Maps:
    - drug_match -> drug_name
    - created_date -> report_date
    - subreddit -> source_context
    - score -> engagement_score
    - Always seriousness = False (observational)
    """
    if df.empty:
        return df
    
    df_normalized = df.copy()
    
    # Map fields
    if "drug_match" in df_normalized.columns and "drug_name" not in df_normalized.columns:
        df_normalized["drug_name"] = df_normalized["drug_match"]
    
    if "created_date" in df_normalized.columns and "report_date" not in df_normalized.columns:
        df_normalized["report_date"] = df_normalized["created_date"]
    
    if "subreddit" in df_normalized.columns and "source_context" not in df_normalized.columns:
        df_normalized["source_context"] = df_normalized["subreddit"]
    
    if "score" in df_normalized.columns and "engagement_score" not in df_normalized.columns:
        df_normalized["engagement_score"] = df_normalized["score"]
    
    # Add required FAERS fields
    if "seriousness" not in df_normalized.columns:
        df_normalized["seriousness"] = False  # Social AE is always observational
    
    if "case_id" not in df_normalized.columns:
        # Generate case IDs from platform + post_id
        df_normalized["case_id"] = (
            "SOCIAL_" + 
            df_normalized.get("platform", "unknown").astype(str) + "_" + 
            df_normalized.get("post_id", "").astype(str)
        )
    
    # Add source marker
    df_normalized["data_source"] = "social_ae"
    
    return df_normalized

