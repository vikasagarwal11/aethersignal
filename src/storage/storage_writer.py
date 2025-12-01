"""
Storage Writer for Unified AE Records
Handles storage to SQLite (local) and provides hooks for Supabase (cloud).
"""

import pandas as pd
import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path("data/ae_records.db")
DB_DIR = DB_PATH.parent


class StorageWriter:
    """
    Writes unified AE records to storage.
    Supports SQLite (local) and provides hooks for Supabase (cloud).
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize storage writer.
        
        Args:
            db_path: Path to SQLite database (default: data/ae_records.db)
        """
        self.db_path = db_path or DB_PATH
        self._ensure_db_directory()
        self._create_table_if_needed()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        DB_DIR.mkdir(parents=True, exist_ok=True)
    
    def _create_table_if_needed(self):
        """Create unified AE records table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create unified AE records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ae_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    drug TEXT,
                    reaction TEXT,
                    confidence REAL,
                    severity REAL,
                    text TEXT,
                    source TEXT,
                    metadata TEXT,
                    drug_key TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_drug (drug),
                    INDEX idx_reaction (reaction),
                    INDEX idx_source (source),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_drug_key (drug_key)
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
    
    def store(self, df: pd.DataFrame, drug: str):
        """
        Store unified AE records to database.
        
        Args:
            df: DataFrame with unified AE entries
            drug: Drug name (for indexing)
        """
        if df.empty:
            logger.info("No records to store")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Add drug_key for easy querying
            df = df.copy()
            df["drug_key"] = drug.lower().strip()
            
            # Convert metadata to JSON string if it's a dict
            if "metadata" in df.columns:
                import json
                df["metadata"] = df["metadata"].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else str(x) if x else "{}"
                )
            
            # Convert timestamp to string
            if "timestamp" in df.columns:
                df["timestamp"] = df["timestamp"].astype(str)
            
            # Store to database
            df.to_sql(
                "ae_records",
                conn,
                if_exists="append",
                index=False,
                method="multi"
            )
            
            conn.close()
            logger.info(f"✓ Stored {len(df)} AE records into DB")
        except Exception as e:
            logger.error(f"Error storing records: {str(e)}")
            raise
    
    def query(self, drug: Optional[str] = None, source: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """
        Query stored AE records.
        
        Args:
            drug: Filter by drug name
            source: Filter by source
            limit: Maximum results
        
        Returns:
            DataFrame with records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM ae_records WHERE 1=1"
            params = []
            
            if drug:
                query += " AND drug_key = ?"
                params.append(drug.lower().strip())
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse metadata JSON if present
            if "metadata" in df.columns:
                import json
                df["metadata"] = df["metadata"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) and x.startswith("{") else {}
                )
            
            return df
        except Exception as e:
            logger.error(f"Error querying records: {str(e)}")
            return pd.DataFrame()
    
    def get_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM ae_records")
            total = cursor.fetchone()[0]
            
            # By source
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM ae_records
                GROUP BY source
            """)
            by_source = {row[0]: row[1] for row in cursor.fetchall()}
            
            # By drug
            cursor.execute("""
                SELECT drug, COUNT(*) as count
                FROM ae_records
                GROUP BY drug
                ORDER BY count DESC
                LIMIT 10
            """)
            top_drugs = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "total_records": total,
                "by_source": by_source,
                "top_drugs": top_drugs
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}

