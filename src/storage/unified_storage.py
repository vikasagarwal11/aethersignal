"""
Unified Storage Engine (Phase 3A.4)
Combines PostgreSQL (structured), Vector Store (embeddings), and Document Store (JSON).
"""

import pandas as pd
import sqlite3
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import Supabase for cloud storage
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class UnifiedStorageEngine:
    """
    Unified storage engine combining:
    - PostgreSQL (structured data)
    - Vector Store (embeddings)
    - Document Store (full-text JSON)
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        supabase_client=None,
        use_supabase: bool = False
    ):
        """
        Initialize unified storage engine.
        
        Args:
            db_path: Path to SQLite database (for local)
            supabase_client: Optional Supabase client (for cloud)
            use_supabase: Whether to use Supabase instead of SQLite
        """
        self.db_path = db_path or Path("data/unified_ae.db")
        self.supabase = supabase_client
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE and supabase_client
        
        if not self.use_supabase:
            self._ensure_db_directory()
            self._create_tables_if_needed()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_tables_if_needed(self):
        """Create unified tables if using SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create ae_events table (simplified for SQLite)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ae_events (
                    ae_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    source_url TEXT,
                    drug_raw TEXT,
                    drug_normalized TEXT NOT NULL,
                    drug_group TEXT,
                    reaction_raw TEXT,
                    reaction_normalized TEXT NOT NULL,
                    reaction_category TEXT,
                    reaction_cluster_id INTEGER,
                    reaction_severity_score REAL,
                    reaction_novelty_score REAL,
                    age INTEGER,
                    age_group TEXT,
                    sex TEXT,
                    country TEXT,
                    dose TEXT,
                    dose_amount REAL,
                    dose_unit TEXT,
                    duration TEXT,
                    onset_time TEXT,
                    route TEXT,
                    seriousness_flags TEXT,  -- JSON string in SQLite
                    outcome TEXT,
                    serious INTEGER DEFAULT 0,
                    event_date TEXT,
                    report_date TEXT,
                    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    full_text TEXT,
                    text_snippet TEXT,
                    embedding_vector TEXT,  -- JSON array in SQLite
                    quantum_score REAL,
                    burst_score REAL,
                    consensus_score REAL,
                    literature_support REAL,
                    clinical_support REAL,
                    label_support REAL,
                    social_support REAL,
                    metadata TEXT,  -- JSON string in SQLite
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_drug ON ae_events(drug_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_reaction ON ae_events(reaction_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_source ON ae_events(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_drug_reaction ON ae_events(drug_normalized, reaction_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_quantum_score ON ae_events(quantum_score)")
            
            # Create drugs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drugs (
                    drug_id TEXT PRIMARY KEY,
                    drug_normalized TEXT NOT NULL UNIQUE,
                    generic_name TEXT,
                    brand_names TEXT,  -- JSON array
                    synonyms TEXT,  -- JSON array
                    drug_group TEXT,
                    mechanism_of_action TEXT,
                    atc_code TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create reactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reactions (
                    reaction_id TEXT PRIMARY KEY,
                    reaction_normalized TEXT NOT NULL UNIQUE,
                    canonical_form TEXT,
                    cluster_id INTEGER,
                    synonyms TEXT,  -- JSON array
                    severity_keywords TEXT,  -- JSON array
                    emoji_keywords TEXT,  -- JSON array
                    category TEXT,
                    soc TEXT,
                    hlt TEXT,
                    pt TEXT,
                    llt TEXT,  -- JSON array
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
    
    def store_ae_event(
        self,
        event: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store a single AE event.
        
        Args:
            event: AE event dictionary
            embedding: Optional embedding vector
        
        Returns:
            AE ID
        """
        import uuid
        
        ae_id = event.get("ae_id") or str(uuid.uuid4())
        event["ae_id"] = ae_id
        
        # Track storage stage (governance integration)
        try:
            from src.evidence_governance.integration import track_storage
            from src.evidence_governance.config import EVIDENCE_GOVERNANCE_ENABLED
            from src.evidence_governance.lineage import get_lineage_tracker
            from src.evidence_governance.provenance import get_provenance_engine
            from src.evidence_governance.quality import get_quality_engine
            from src.evidence_governance.fusion import get_fusion_engine
            
            if EVIDENCE_GOVERNANCE_ENABLED:
                source = event.get("source", "unknown")
                event = track_storage(event, source)
                
                # Calculate governance scores
                record_id = event.get("ae_id") or event.get("record_id")
                lineage = get_lineage_tracker()
                lineage_chain = lineage.get_lineage(record_id) if record_id else []
                
                # Provenance scoring
                provenance_engine = get_provenance_engine()
                prov_score = provenance_engine.score(event, lineage_chain)
                event["provenance"] = prov_score
                
                # Quality scoring
                quality_engine = get_quality_engine()
                qual_score = quality_engine.score(event, lineage_chain)
                event["data_quality"] = qual_score
                
                # Fusion (Evidence Strength Score)
                fusion_engine = get_fusion_engine()
                # Try to get novelty engine if available
                novelty_engine = None
                try:
                    from src.ai.novelty_detection import NoveltyDetectionEngine
                    novelty_engine = NoveltyDetectionEngine()
                except ImportError:
                    pass
                
                ess = fusion_engine.fuse(prov_score, qual_score, event, novelty_engine)
                event["evidence_strength"] = ess
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Governance scoring error: {e}")
            pass  # Governance optional
        
        # Prepare event for storage
        if self.use_supabase:
            return self._store_to_supabase(event, embedding)
        else:
            return self._store_to_sqlite(event, embedding)
    
    def _store_to_supabase(self, event: Dict[str, Any], embedding: Optional[List[float]]) -> str:
        """Store to Supabase."""
        try:
            # Convert embedding to list if numpy array
            if embedding is not None:
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                event["embedding_vector"] = embedding
            
            # Convert JSONB fields
            if "seriousness_flags" in event and isinstance(event["seriousness_flags"], dict):
                event["seriousness_flags"] = json.dumps(event["seriousness_flags"])
            
            if "metadata" in event and isinstance(event["metadata"], dict):
                event["metadata"] = json.dumps(event["metadata"])
            
            # Store
            result = self.supabase.table("ae_events").insert(event).execute()
            return event["ae_id"]
        except Exception as e:
            logger.error(f"Error storing to Supabase: {str(e)}")
            raise
    
    def _store_to_sqlite(self, event: Dict[str, Any], embedding: Optional[List[float]]) -> str:
        """Store to SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert embedding to JSON string
            if embedding is not None:
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                event["embedding_vector"] = json.dumps(embedding)
            
            # Convert JSONB fields to JSON strings
            if "seriousness_flags" in event:
                if isinstance(event["seriousness_flags"], dict):
                    event["seriousness_flags"] = json.dumps(event["seriousness_flags"])
                elif event["seriousness_flags"] is None:
                    event["seriousness_flags"] = "{}"
            
            if "metadata" in event:
                if isinstance(event["metadata"], dict):
                    event["metadata"] = json.dumps(event["metadata"])
                elif event["metadata"] is None:
                    event["metadata"] = "{}"
            
            # Convert dates to strings
            for date_field in ["event_date", "report_date", "fetched_at", "created_at", "updated_at"]:
                if date_field in event and event[date_field]:
                    if isinstance(event[date_field], datetime):
                        event[date_field] = event[date_field].isoformat()
            
            # Insert
            columns = ", ".join(event.keys())
            placeholders = ", ".join(["?" for _ in event])
            values = list(event.values())
            
            cursor.execute(
                f"INSERT OR REPLACE INTO ae_events ({columns}) VALUES ({placeholders})",
                values
            )
            
            conn.commit()
            conn.close()
            
            return event["ae_id"]
        except Exception as e:
            logger.error(f"Error storing to SQLite: {str(e)}")
            raise
    
    def store_ae_events_batch(
        self,
        events: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Store multiple AE events in batch.
        
        Args:
            events: List of AE event dictionaries
            embeddings: Optional list of embedding vectors
        
        Returns:
            List of AE IDs
        """
        ae_ids = []
        
        for i, event in enumerate(events):
            embedding = embeddings[i] if embeddings and i < len(embeddings) else None
            ae_id = self.store_ae_event(event, embedding)
            ae_ids.append(ae_id)
        
        return ae_ids
    
    def store_drug(self, drug: Dict[str, Any]) -> str:
        """Store or update a drug entry."""
        import uuid
        
        drug_id = drug.get("drug_id") or str(uuid.uuid4())
        drug["drug_id"] = drug_id
        
        if self.use_supabase:
            try:
                self.supabase.table("drugs").upsert(drug).execute()
                return drug_id
            except Exception as e:
                logger.error(f"Error storing drug to Supabase: {str(e)}")
                raise
        else:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Convert arrays to JSON strings
                for field in ["brand_names", "synonyms"]:
                    if field in drug and isinstance(drug[field], list):
                        drug[field] = json.dumps(drug[field])
                
                columns = ", ".join(drug.keys())
                placeholders = ", ".join(["?" for _ in drug])
                values = list(drug.values())
                
                cursor.execute(
                    f"INSERT OR REPLACE INTO drugs ({columns}) VALUES ({placeholders})",
                    values
                )
                
                conn.commit()
                conn.close()
                return drug_id
            except Exception as e:
                logger.error(f"Error storing drug to SQLite: {str(e)}")
                raise
    
    def store_reaction(self, reaction: Dict[str, Any]) -> str:
        """Store or update a reaction entry."""
        import uuid
        
        reaction_id = reaction.get("reaction_id") or str(uuid.uuid4())
        reaction["reaction_id"] = reaction_id
        
        if self.use_supabase:
            try:
                self.supabase.table("reactions").upsert(reaction).execute()
                return reaction_id
            except Exception as e:
                logger.error(f"Error storing reaction to Supabase: {str(e)}")
                raise
        else:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Convert arrays to JSON strings
                for field in ["synonyms", "severity_keywords", "emoji_keywords", "llt"]:
                    if field in reaction and isinstance(reaction[field], list):
                        reaction[field] = json.dumps(reaction[field])
                
                columns = ", ".join(reaction.keys())
                placeholders = ", ".join(["?" for _ in reaction])
                values = list(reaction.values())
                
                cursor.execute(
                    f"INSERT OR REPLACE INTO reactions ({columns}) VALUES ({placeholders})",
                    values
                )
                
                conn.commit()
                conn.close()
                return reaction_id
            except Exception as e:
                logger.error(f"Error storing reaction to SQLite: {str(e)}")
                raise

