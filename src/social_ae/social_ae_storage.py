"""
SQLite storage module for Social AE posts.
Handles persistence, deduplication, and historical tracking.
"""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


# Database file location
DB_DIR = Path("data/social_ae")
DB_FILE = DB_DIR / "social_posts.db"


def init_database():
    """Initialize SQLite database with schema."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create main posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            post_id TEXT NOT NULL,
            post_url TEXT,
            raw_text TEXT NOT NULL,
            cleaned_text TEXT,
            created_utc INTEGER,
            created_date TIMESTAMP,
            drug_match TEXT,
            reaction TEXT,
            meddra_pt TEXT,
            meddra_pt_code TEXT,
            confidence_score REAL,
            subreddit TEXT,
            author_hash TEXT,
            score INTEGER,
            is_anonymized BOOLEAN DEFAULT 0,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, post_id)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_drug_match ON social_posts(drug_match)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reaction ON social_posts(reaction)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_utc ON social_posts(created_utc)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fetched_at ON social_posts(fetched_at)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_platform_post_id ON social_posts(platform, post_id)
    """)
    
    # Create pull history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pull_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pull_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            drug_terms TEXT,
            platforms TEXT,
            posts_fetched INTEGER,
            posts_new INTEGER,
            posts_duplicate INTEGER,
            status TEXT,
            error_message TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def hash_username(username: str) -> str:
    """Hash username for anonymization."""
    if not username or username == "[deleted]" or username == "unknown":
        return "[anonymous]"
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def store_posts(posts: List[Dict], drug_terms: str, platforms: List[str]) -> Dict:
    """
    Store posts in database with deduplication.
    
    Args:
        posts: List of post dictionaries
        drug_terms: Comma-separated drug terms
        platforms: List of platforms used
    
    Returns:
        Dictionary with storage statistics
    """
    if not posts:
        return {"stored": 0, "duplicates": 0, "errors": 0}
    
    init_database()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    stored = 0
    duplicates = 0
    errors = 0
    
    for post in posts:
        try:
            # Prepare data
            platform = post.get("platform", post.get("source", "unknown"))
            post_id = str(post.get("post_id", ""))
            raw_text = post.get("text", post.get("raw_text", ""))
            cleaned_text = post.get("cleaned_text", raw_text)
            created_utc = post.get("created_utc")
            created_date = post.get("created_date")
            drug_match = post.get("drug_match", "")
            reaction = post.get("reaction")
            meddra_pt = post.get("meddra_pt")
            meddra_pt_code = post.get("meddra_pt_code")
            confidence_score = post.get("confidence_score")
            subreddit = post.get("subreddit", "")
            author = post.get("author", "")
            author_hash = hash_username(author)
            score = post.get("score", 0)
            post_url = post.get("url", "")
            is_anonymized = post.get("is_anonymized", False)
            
            # Convert created_date if it's a datetime object
            if created_date and isinstance(created_date, datetime):
                created_date = created_date.isoformat()
            elif created_utc:
                try:
                    created_date = datetime.fromtimestamp(created_utc).isoformat()
                except (ValueError, OSError):
                    created_date = None
            
            # Try to insert (will fail on duplicate)
            cursor.execute("""
                INSERT OR IGNORE INTO social_posts (
                    platform, post_id, post_url, raw_text, cleaned_text,
                    created_utc, created_date, drug_match, reaction,
                    meddra_pt, meddra_pt_code, confidence_score,
                    subreddit, author_hash, score, is_anonymized
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                platform, post_id, post_url, raw_text, cleaned_text,
                created_utc, created_date, drug_match, reaction,
                meddra_pt, meddra_pt_code, confidence_score,
                subreddit, author_hash, score, is_anonymized
            ))
            
            if cursor.rowcount > 0:
                stored += 1
            else:
                duplicates += 1
                
        except Exception as e:
            errors += 1
            continue
    
    # Log pull history
    cursor.execute("""
        INSERT INTO pull_history (
            drug_terms, platforms, posts_fetched, posts_new, posts_duplicate, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        drug_terms,
        ",".join(platforms),
        len(posts),
        stored,
        duplicates,
        "success" if errors == 0 else f"partial ({errors} errors)"
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "stored": stored,
        "duplicates": duplicates,
        "errors": errors,
        "total": len(posts)
    }


def get_posts(
    drug_match: Optional[str] = None,
    reaction: Optional[str] = None,
    platform: Optional[str] = None,
    days_back: Optional[int] = None,
    min_confidence: Optional[float] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Retrieve posts from database with filters.
    
    Args:
        drug_match: Filter by drug name
        reaction: Filter by reaction
        platform: Filter by platform
        days_back: Get posts from last N days
        min_confidence: Minimum confidence score
        limit: Maximum number of posts to return
    
    Returns:
        DataFrame with posts
    """
    init_database()
    conn = sqlite3.connect(DB_FILE)
    
    query = "SELECT * FROM social_posts WHERE 1=1"
    params = []
    
    if drug_match:
        query += " AND drug_match LIKE ?"
        params.append(f"%{drug_match}%")
    
    if reaction:
        query += " AND reaction = ?"
        params.append(reaction)
    
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    
    if days_back:
        cutoff_timestamp = int((datetime.now().timestamp() - (days_back * 86400)))
        query += " AND created_utc >= ?"
        params.append(cutoff_timestamp)
    
    if min_confidence is not None:
        query += " AND confidence_score >= ?"
        params.append(min_confidence)
    
    query += " ORDER BY created_utc DESC LIMIT ?"
    params.append(limit)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def get_statistics() -> Dict:
    """Get database statistics."""
    init_database()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total posts
    cursor.execute("SELECT COUNT(*) FROM social_posts")
    stats["total_posts"] = cursor.fetchone()[0]
    
    # Posts by platform
    cursor.execute("""
        SELECT platform, COUNT(*) 
        FROM social_posts 
        GROUP BY platform
    """)
    stats["by_platform"] = dict(cursor.fetchall())
    
    # Posts with reactions
    cursor.execute("SELECT COUNT(*) FROM social_posts WHERE reaction IS NOT NULL")
    stats["with_reactions"] = cursor.fetchone()[0]
    
    # Unique drugs
    cursor.execute("SELECT COUNT(DISTINCT drug_match) FROM social_posts WHERE drug_match IS NOT NULL")
    stats["unique_drugs"] = cursor.fetchone()[0]
    
    # Unique reactions
    cursor.execute("SELECT COUNT(DISTINCT reaction) FROM social_posts WHERE reaction IS NOT NULL")
    stats["unique_reactions"] = cursor.fetchone()[0]
    
    # Date range
    cursor.execute("SELECT MIN(created_utc), MAX(created_utc) FROM social_posts WHERE created_utc IS NOT NULL")
    date_range = cursor.fetchone()
    if date_range[0] and date_range[1]:
        stats["date_range"] = {
            "earliest": datetime.fromtimestamp(date_range[0]).isoformat(),
            "latest": datetime.fromtimestamp(date_range[1]).isoformat()
        }
    
    # Pull history
    cursor.execute("SELECT COUNT(*) FROM pull_history")
    stats["total_pulls"] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT pull_date, posts_new, status 
        FROM pull_history 
        ORDER BY pull_date DESC 
        LIMIT 10
    """)
    stats["recent_pulls"] = [
        {"date": row[0], "new_posts": row[1], "status": row[2]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return stats


def clear_old_posts(days_to_keep: int = 90):
    """Clear posts older than specified days."""
    init_database()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cutoff_timestamp = int((datetime.now().timestamp() - (days_to_keep * 86400)))
    
    cursor.execute("DELETE FROM social_posts WHERE created_utc < ?", (cutoff_timestamp,))
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted

