"""
Unified AE Data Loader - Phase 3J
Loads and normalizes data from all sources into unified schema.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .config import load_config, is_source_enabled

logger = logging.getLogger(__name__)


def load_unified_ae_data(
    drug: Optional[str] = None,
    days_back: int = 90,
    sources: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load unified AE data from all enabled sources.
    
    Args:
        drug: Optional drug filter
        days_back: Number of days to look back
        sources: Optional list of specific sources to load
    
    Returns:
        Unified DataFrame with normalized schema
    """
    config = load_config()
    all_dfs = []
    
    # Determine which sources to load
    if sources is None:
        sources_to_load = [
            name for name, enabled in config.get("sources", {}).items()
            if enabled
        ]
    else:
        sources_to_load = sources
    
    # Load from unified storage (if available)
    try:
        from src.storage.unified_storage import UnifiedStorageEngine
        
        storage = UnifiedStorageEngine()
        
        # Query unified database using SQLite
        if not storage.use_supabase:
            # Use SQLite query
            import sqlite3
            conn = sqlite3.connect(storage.db_path)
            
            query = "SELECT * FROM ae_events WHERE 1=1"
            params = []
            
            if drug:
                query += " AND drug_normalized LIKE ?"
                params.append(f"%{drug}%")
            
            if days_back:
                cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                query += " AND event_date >= ?"
                params.append(cutoff_date)
            
            unified_df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if not unified_df.empty:
                # Normalize schema
                unified_df = _normalize_schema(unified_df)
                all_dfs.append(unified_df)
                logger.info(f"Loaded {len(unified_df)} records from unified storage")
    except Exception as e:
        logger.debug(f"Unified storage not available: {e}")
    
    # Fallback: Load from individual sources if unified storage unavailable
    if not all_dfs:
        # Try AEPipeline as fallback (integrates all sources)
        try:
            from src.ae_pipeline import AEPipeline
            
            pipeline = AEPipeline()
            pipeline_df = pipeline.run(
                drug=drug or "all",
                days_back=days_back,
                include_social=True,
                include_faers=True,
                include_literature=True,
                include_free_apis=True,
                store_results=False
            )
            
            if not pipeline_df.empty:
                pipeline_df = _normalize_schema(pipeline_df)
                all_dfs.append(pipeline_df)
                logger.info(f"Loaded {len(pipeline_df)} records from AEPipeline")
        except Exception as e:
            logger.debug(f"AEPipeline load failed: {e}")
    
    # Merge all dataframes
    if not all_dfs:
        logger.warning("No data loaded from any source")
        return _create_empty_dataframe()
    
    merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
    
    # Additional normalization
    merged_df = _normalize_schema(merged_df)
    
    # Filter by drug if specified
    if drug:
        merged_df = merged_df[
            merged_df["drug"].str.contains(drug, case=False, na=False)
        ]
    
    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=days_back)
    if "created_date" in merged_df.columns:
        merged_df["created_date"] = pd.to_datetime(merged_df["created_date"], errors="coerce")
        merged_df = merged_df[merged_df["created_date"] >= cutoff_date]
    
    logger.info(f"Loaded {len(merged_df)} unified AE records")
    
    return merged_df


def _normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame to unified executive dashboard schema.
    
    Unified schema:
    - drug: str
    - reaction: str
    - reaction_pt: str (normalized preferred term)
    - source: str
    - severity_score: float (0-1)
    - quantum_score: float (0-1)
    - confidence: float (0-1)
    - created_date: datetime
    - country: str (optional)
    - text: str (optional)
    - mechanism_label: str (optional)
    """
    normalized = df.copy()
    
    # Ensure required columns exist
    required_cols = {
        "drug": "drug_name",
        "reaction": "reaction",
        "source": "source",
        "created_date": "timestamp"
    }
    
    for target_col, possible_sources in required_cols.items():
        if target_col not in normalized.columns:
            # Try alternative column names
            for alt in possible_sources.split("|"):
                if alt in normalized.columns:
                    normalized[target_col] = normalized[alt]
                    break
            else:
                # Create default if not found
                if target_col == "source":
                    normalized[target_col] = "unknown"
                elif target_col == "created_date":
                    normalized[target_col] = datetime.now()
                else:
                    normalized[target_col] = ""
    
    # Normalize drug names
    if "drug" in normalized.columns:
        normalized["drug"] = normalized["drug"].str.strip().str.title()
    
    # Normalize reaction to PT if available
    if "reaction_pt" not in normalized.columns:
        if "reaction_normalized" in normalized.columns:
            normalized["reaction_pt"] = normalized["reaction_normalized"]
        else:
            normalized["reaction_pt"] = normalized.get("reaction", "")
    
    # Ensure numeric scores exist
    for score_col in ["severity_score", "quantum_score", "confidence"]:
        if score_col not in normalized.columns:
            normalized[score_col] = 0.0
        else:
            normalized[score_col] = pd.to_numeric(normalized[score_col], errors="coerce").fillna(0.0)
    
    # Ensure country exists
    if "country" not in normalized.columns:
        normalized["country"] = "unknown"
    
    # Ensure text exists
    if "text" not in normalized.columns:
        normalized["text"] = normalized.get("full_text", "")
    
    # Ensure mechanism_label exists
    if "mechanism_label" not in normalized.columns:
        normalized["mechanism_label"] = ""
    
    return normalized


def _create_empty_dataframe() -> pd.DataFrame:
    """Create empty DataFrame with unified schema."""
    return pd.DataFrame({
        "drug": [],
        "reaction": [],
        "reaction_pt": [],
        "source": [],
        "severity_score": [],
        "quantum_score": [],
        "confidence": [],
        "created_date": [],
        "country": [],
        "text": [],
        "mechanism_label": []
    })


def _load_faers_fallback(drug: Optional[str], days_back: int) -> pd.DataFrame:
    """Fallback FAERS loader."""
    try:
        from src.local_faers.faers_local_engine import FAERSLocalEngine
        
        engine = FAERSLocalEngine()
        # Query FAERS data
        # This is a placeholder - adjust based on actual FAERS engine API
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _load_social_fallback(drug: Optional[str], days_back: int) -> pd.DataFrame:
    """Fallback Social AE loader."""
    try:
        from src.social_ae.social_ae_storage import load_social_ae_data
        
        # Load social AE data
        # This is a placeholder - adjust based on actual social AE storage API
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _load_literature_fallback(drug: Optional[str], days_back: int) -> pd.DataFrame:
    """Fallback Literature loader."""
    try:
        from src.literature_integration import load_literature_data
        
        # Load literature data
        # This is a placeholder - adjust based on actual literature API
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

