"""
AetherSignal Unified AE Ingestion Pipeline
Master orchestrator that aggregates adverse events from all sources:
- Social media (Reddit, X)
- FAERS
- Literature (PubMed, ClinicalTrials)
- Free APIs (OpenFDA, EMA, DailyMed, etc.)
- Paid APIs (auto-disabled until keys exist)
"""

import pandas as pd
import datetime
import traceback
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.data_sources import DataSourceManagerV2
from src.data_sources.unified_integration import UnifiedSourceIntegration
from src.social_ae.social_fetcher import fetch_reddit_posts, fetch_x_posts
from src.social_ae.social_mapper import extract_reactions_from_posts
from src.social_ae.social_cleaner import clean_and_normalize_posts
from src.literature_integration import search_pubmed, search_clinical_trials
from src.storage.storage_writer import StorageWriter

# Evidence governance integration (optional)
try:
    from src.evidence_governance.pipeline_integration import (
        track_social_ingestion,
        track_social_cleaning,
        track_social_normalization,
        track_social_reaction_extraction,
        track_literature_ingestion,
        track_faers_ingestion,
        track_scoring
    )
    EVIDENCE_GOVERNANCE_AVAILABLE = True
except ImportError:
    EVIDENCE_GOVERNANCE_AVAILABLE = False
    # No-op functions if governance not available
    def track_social_ingestion(x): return x
    def track_social_cleaning(x): return x
    def track_social_normalization(x): return x
    def track_social_reaction_extraction(x): return x
    def track_literature_ingestion(x): return x
    def track_faers_ingestion(x): return x
    def track_scoring(x, y): return x

logger = logging.getLogger(__name__)


class SocialAEEngine:
    """
    Wrapper for Social AE processing.
    Fetches, cleans, and extracts reactions from social media.
    """
    
    def search(self, drug: str, days_back: int = 30, platforms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search social media for adverse events.
        
        Args:
            drug: Drug name to search
            days_back: Days to look back
            platforms: List of platforms (default: ["reddit", "x"])
        
        Returns:
            List of unified AE entries
        """
        if platforms is None:
            platforms = ["reddit", "x"]
        
        all_posts = []
        
        # Fetch from Reddit
        if "reddit" in platforms:
            try:
                reddit_posts = fetch_reddit_posts(
                    drug_terms=[drug],
                    limit_per_term=50,
                    days_back=days_back
                )
                for post in reddit_posts:
                    post["platform"] = "reddit"
                    # Track ingestion
                    if EVIDENCE_GOVERNANCE_AVAILABLE:
                        post = track_social_ingestion(post)
                all_posts.extend(reddit_posts)
            except Exception as e:
                logger.warning(f"Reddit fetch error: {str(e)}")
        
        # Fetch from X (Twitter)
        if "x" in platforms or "twitter" in platforms:
            try:
                x_posts = fetch_x_posts(
                    drug_terms=[drug],
                    limit_per_term=50,
                    days_back=days_back
                )
                for post in x_posts:
                    post["platform"] = "x"
                    # Track ingestion
                    if EVIDENCE_GOVERNANCE_AVAILABLE:
                        post = track_social_ingestion(post)
                all_posts.extend(x_posts)
            except Exception as e:
                logger.warning(f"X fetch error: {str(e)}")
        
        if not all_posts:
            return []
        
        # Clean and normalize
        try:
            df = clean_and_normalize_posts(all_posts)
            if df.empty:
                return []
        except Exception as e:
            logger.warning(f"Social cleaning error: {str(e)}")
            return []
        
        # Extract reactions
        try:
            df = extract_reactions_from_posts(df, include_confidence=True)
            if df.empty:
                return []
        except Exception as e:
            logger.warning(f"Reaction extraction error: {str(e)}")
            return []
        
        # Convert to unified format
        results = []
        for _, row in df.iterrows():
            reactions = row.get("reactions", [])
            if isinstance(reactions, str):
                reactions = [reactions]
            elif not isinstance(reactions, list):
                reactions = []
            
            # Create one entry per reaction
            for reaction in reactions:
                if isinstance(reaction, dict):
                    reaction_name = reaction.get("reaction", "")
                    confidence = reaction.get("confidence", 0.5)
                else:
                    reaction_name = str(reaction)
                    confidence = row.get("confidence_score", 0.5)
                
                results.append({
                    "timestamp": row.get("created_date") or row.get("created_utc"),
                    "drug": drug,
                    "reaction": reaction_name,
                    "confidence": float(confidence),
                    "severity": row.get("severity_score", 0.0),
                    "text": row.get("text", ""),
                    "source": f"social_{row.get('platform', 'unknown')}",
                    "metadata": {
                        "platform": row.get("platform"),
                        "post_id": row.get("post_id"),
                        "url": row.get("url"),
                        "score": row.get("score", 0)
                    }
                })
        
        return results


class FAERSEngine:
    """
    Wrapper for FAERS processing.
    Searches local FAERS data or uses OpenFDA API.
    """
    
    def __init__(self):
        """Initialize FAERS engine."""
        self.local_engine = None
        try:
            from src.local_faers import FaersLocalEngine
            self.local_engine = FaersLocalEngine()
        except ImportError:
            logger.info("Local FAERS engine not available, will use OpenFDA API only")
    
    def search(self, drug: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Search FAERS for adverse events.
        
        Args:
            drug: Drug name to search
            limit: Maximum results
        
        Returns:
            List of unified AE entries
        """
        results = []
        
        # Try local FAERS first if available
        if self.local_engine and self.local_engine.joined:
            try:
                df = self.local_engine.joined.data
                if not df.empty and "drug" in df.columns:
                    # Filter by drug
                    drug_df = df[df["drug"].str.contains(drug, case=False, na=False)]
                    
                    for _, row in drug_df.head(limit).iterrows():
                        results.append({
                            "timestamp": row.get("event_dt") or row.get("init_fda_dt"),
                            "drug": drug,
                            "reaction": row.get("pt") or row.get("reaction"),
                            "confidence": 0.9,  # FAERS is high confidence
                            "severity": 0.5,  # Default, can be enhanced
                            "text": f"FAERS case {row.get('primaryid', 'unknown')}",
                            "source": "faers",
                            "metadata": {
                                "primaryid": row.get("primaryid"),
                                "caseid": row.get("caseid"),
                                "outcome": row.get("outc_cod"),
                                "serious": row.get("serious", 0)
                            }
                        })
            except Exception as e:
                logger.warning(f"Local FAERS search error: {str(e)}")
        
        # If no local results, FAERS will be covered by OpenFDA in multi-source fetch
        return results


class LiteratureEngine:
    """
    Wrapper for Literature processing.
    Searches PubMed and ClinicalTrials.gov.
    """
    
    def search(self, drug: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search literature for adverse events.
        
        Args:
            drug: Drug name to search
            limit: Maximum results
        
        Returns:
            List of unified AE entries
        """
        results = []
        
        # Search PubMed
        try:
            pubmed_results = search_pubmed(drug, max_results=min(limit, 20))
            for article in pubmed_results:
                results.append({
                    "timestamp": article.get("pub_date"),
                    "drug": drug,
                    "reaction": "reported adverse effect",
                    "confidence": 0.8,  # Literature is high confidence
                    "severity": 0.5,
                    "text": article.get("title", "") + " " + article.get("abstract", ""),
                    "source": "pubmed",
                    "metadata": {
                        "pmid": article.get("pmid"),
                        "title": article.get("title"),
                        "authors": article.get("authors"),
                        "journal": article.get("journal")
                    }
                })
        except Exception as e:
            logger.warning(f"PubMed search error: {str(e)}")
        
        # Search ClinicalTrials
        try:
            trials_results = search_clinical_trials(drug, max_results=min(limit, 20))
            for trial in trials_results:
                results.append({
                    "timestamp": trial.get("start_date"),
                    "drug": drug,
                    "reaction": "clinical trial adverse event",
                    "confidence": 0.7,
                    "severity": 0.4,
                    "text": trial.get("title", "") + " " + trial.get("summary", ""),
                    "source": "clinicaltrials",
                    "metadata": {
                        "nct_id": trial.get("nct_id"),
                        "title": trial.get("title"),
                        "status": trial.get("status")
                    }
                })
        except Exception as e:
            logger.warning(f"ClinicalTrials search error: {str(e)}")
        
        return results


class AEPipeline:
    """
    Master orchestrator for unified AE ingestion.
    Aggregates data from all sources and returns unified format.
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize the AE pipeline.
        
        Args:
            supabase_client: Optional Supabase client for vector store
        """
        self.ds_manager = DataSourceManagerV2()
        self.unified_integration = UnifiedSourceIntegration(
            ds_manager=self.ds_manager,
            supabase_client=supabase_client
        )
        self.social_engine = SocialAEEngine()
        self.faers_engine = FAERSEngine()
        self.lit_engine = LiteratureEngine()
        self.storage = StorageWriter()
    
    def run(
        self,
        drug: str,
        days_back: int = 30,
        include_social: bool = True,
        include_faers: bool = True,
        include_literature: bool = True,
        include_free_apis: bool = True,
        store_results: bool = True
    ) -> pd.DataFrame:
        """
        Run the complete AE ingestion pipeline.
        
        Args:
            drug: Drug name to search
            days_back: Days to look back (for social media)
            include_social: Include social media sources
            include_faers: Include FAERS data
            include_literature: Include literature sources
            include_free_apis: Include free API sources (OpenFDA, EMA, etc.)
            store_results: Whether to store results in database
        
        Returns:
            DataFrame with unified AE entries
        """
        logger.info(f"\n🚀 Running AE Pipeline for: {drug}")
        
        all_entries = []
        
        # -----------------------------------------------------
        # 1. Social AE Engine
        # -----------------------------------------------------
        if include_social:
            try:
                social = self.social_engine.search(drug, days_back=days_back)
                logger.info(f"✓ Social AE: {len(social)} records")
                all_entries.extend(social)
            except Exception as e:
                logger.warning(f"[WARN] Social AE error: {e}")
                logger.debug(traceback.format_exc())
        
        # -----------------------------------------------------
        # 2. FAERS Engine
        # -----------------------------------------------------
        if include_faers:
            try:
                faers = self.faers_engine.search(drug)
                logger.info(f"✓ FAERS: {len(faers)} records")
                all_entries.extend(faers)
            except Exception as e:
                logger.warning(f"[WARN] FAERS error: {e}")
                logger.debug(traceback.format_exc())
        
        # -----------------------------------------------------
        # 3. Literature Engine
        # -----------------------------------------------------
        if include_literature:
            try:
                lit = self.lit_engine.search(drug)
                logger.info(f"✓ Literature: {len(lit)} records")
                all_entries.extend(lit)
            except Exception as e:
                logger.warning(f"[WARN] Literature error: {e}")
                logger.debug(traceback.format_exc())
        
        # -----------------------------------------------------
        # 4. Free Data Sources (OpenFDA, EMA, DailyMed, etc.)
        # Using Unified Integration for normalization + embeddings
        # -----------------------------------------------------
        if include_free_apis:
            try:
                # Use unified integration to get normalized, embedded reactions
                normalized_df = self.unified_integration.fetch_and_normalize(
                    drug=drug,
                    days_back=days_back
                )
                
                if not normalized_df.empty:
                    # Convert DataFrame back to list format for consistency
                    multi = normalized_df.to_dict("records")
                    logger.info(f"✓ External Free APIs (normalized): {len(multi)} records")
                    all_entries.extend(multi)
                else:
                    # Fallback to direct fetch if normalization fails
                    query = {
                        "drug_name": drug,
                        "drug": drug,
                        "limit": 100
                    }
                    multi = self.ds_manager.fetch_all(query)
                    logger.info(f"✓ External Free APIs (fallback): {len(multi)} records")
                    all_entries.extend(multi)
            except Exception as e:
                logger.warning(f"[WARN] Multi-source error: {e}")
                logger.debug(traceback.format_exc())
        
        # -----------------------------------------------------
        # COMBINE + CLEAN
        # -----------------------------------------------------
        if not all_entries:
            logger.info("No entries found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_entries)
        df = self._postprocess(df)
        
        # -----------------------------------------------------
        # STORAGE
        # -----------------------------------------------------
        if store_results and not df.empty:
            try:
                self.storage.store(df, drug)
                logger.info(f"✓ Stored {len(df)} records to database")
            except Exception as e:
                logger.warning(f"[WARN] Storage error: {e}")
        
        logger.info(f"✓ Pipeline complete: {len(df)} total unified entries")
        return df
    
    def _postprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Postprocess unified entries: normalize types, dedupe, sort.
        
        Args:
            df: Raw DataFrame with entries
        
        Returns:
            Cleaned and deduplicated DataFrame
        """
        if df.empty:
            return df
        
        # Normalize timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        
        # Fill missing values
        df["reaction"] = df["reaction"].fillna("Unknown")
        df["drug"] = df["drug"].fillna("Unknown")
        df["text"] = df["text"].fillna("")
        
        # Ensure numeric columns
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.5)
        df["severity"] = pd.to_numeric(df["severity"], errors="coerce").fillna(0.0)
        
        # Remove duplicates by (drug, reaction, text signature)
        # Use first 200 chars of text for deduplication
        df["hash"] = (
            df["drug"].astype(str) + "_" +
            df["reaction"].astype(str) + "_" +
            df["text"].astype(str).str[:200]
        )
        df = df.drop_duplicates(subset="hash", keep="first")
        
        # Sort by timestamp (newest first)
        df = df.sort_values(by="timestamp", ascending=False, na_position="last")
        
        # Drop hash column
        df = df.drop(columns=["hash"], errors="ignore")
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df

