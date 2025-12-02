"""
Public Daily Pull - Unified daily pull for all free sources.
Pulls data from all free sources and stores in public_ae_data table.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

from src.data_sources.registry import SourceRegistry
from src.storage.public_data_storage import store_public_ae_data
from src.social_ae.social_ae_scheduler import DEFAULT_DRUG_WATCHLIST

logger = logging.getLogger(__name__)


def run_public_daily_pull(
    drug_terms: Optional[List[str]] = None,
    days_back: int = 1,
    limit_per_drug: int = 100
) -> Dict[str, Any]:
    """
    Run daily pull from ALL free sources and store in public_ae_data.
    
    Sources included:
    - Reddit (social)
    - OpenFDA (FAERS)
    - PubMed (literature)
    - ClinicalTrials.gov (trials)
    - DailyMed (labels)
    - MedSafetyAlerts (RSS feeds)
    
    Args:
        drug_terms: List of drug names (defaults to watchlist)
        days_back: Days back to search
        limit_per_drug: Max results per drug per source
    
    Returns:
        Dictionary with pull results
    """
    if drug_terms is None:
        drug_terms = DEFAULT_DRUG_WATCHLIST
    
    logger.info(f"Starting public daily pull for {len(drug_terms)} drugs")
    
    all_results = []
    source_stats = {}
    
    try:
        # Initialize source registry
        registry = SourceRegistry()
        
        # Pull from each source
        sources_to_pull = [
            ("openfda", "OpenFDA"),
            ("pubmed", "PubMed"),
            ("clinicaltrials", "ClinicalTrials.gov"),
            ("dailymed", "DailyMed"),
            ("medsafety_alerts", "MedSafetyAlerts")
        ]
        
        for source_key, source_name in sources_to_pull:
            if source_key not in registry.sources:
                logger.warning(f"Source {source_name} not available, skipping")
                continue
            
            source_client = registry.sources[source_key]
            source_results = []
            
            try:
                logger.info(f"Pulling from {source_name}...")
                
                for drug in drug_terms:
                    try:
                        query = {
                            "drug_name": drug,
                            "limit": limit_per_drug,
                            "days_back": days_back
                        }
                        
                        results = source_client.fetch(query)
                        source_results.extend(results)
                        
                        logger.info(f"  {drug}: {len(results)} results from {source_name}")
                    
                    except Exception as e:
                        logger.warning(f"Error fetching {drug} from {source_name}: {str(e)}")
                        continue
                
                source_stats[source_key] = {
                    "name": source_name,
                    "results": len(source_results),
                    "success": True
                }
                
                all_results.extend(source_results)
            
            except Exception as e:
                logger.error(f"Error pulling from {source_name}: {str(e)}")
                source_stats[source_key] = {
                    "name": source_name,
                    "results": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Also pull from social sources (Reddit, YouTube)
        logger.info("Pulling from social sources...")
        try:
            from src.social_ae.social_fetcher import fetch_daily_social_posts
            from src.social_ae.social_cleaner import clean_and_normalize_posts
            from src.social_ae.social_mapper import extract_reactions_from_posts
            
            drug_terms_str = ", ".join(drug_terms)
            raw_posts = fetch_daily_social_posts(
                drug_terms_str,
                platforms=["reddit", "youtube"],  # Skip X/Twitter (requires paid API)
                limit_per_term=limit_per_drug,
                days_back=days_back
            )
            
            if raw_posts:
                cleaned_df = clean_and_normalize_posts(raw_posts)
                if not cleaned_df.empty:
                    df_with_reactions = extract_reactions_from_posts(cleaned_df, include_confidence=True)
                    
                    # Convert to unified format
                    for _, row in df_with_reactions.iterrows():
                        all_results.append({
                            "drug": row.get("drug_match", ""),
                            "reaction": row.get("reaction", ""),
                            "source": f"social_{row.get('platform', 'reddit')}",
                            "text": row.get("cleaned_text", row.get("text", "")),
                            "timestamp": row.get("created_date", datetime.now()).isoformat() if isinstance(row.get("created_date"), datetime) else str(row.get("created_date", datetime.now())),
                            "confidence": float(row.get("ae_prob", row.get("confidence_score", 0.5))),
                            "severity": float(row.get("severity_score", 0.0)),
                            "metadata": {
                                "platform": row.get("platform", "reddit"),
                                "subreddit": row.get("subreddit", ""),
                                "score": int(row.get("score", 0))
                            }
                        })
            
            source_stats["social"] = {
                "name": "Social Media (Reddit/YouTube)",
                "results": len(raw_posts) if raw_posts else 0,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error pulling from social sources: {str(e)}")
            source_stats["social"] = {
                "name": "Social Media",
                "results": 0,
                "success": False,
                "error": str(e)
            }
        
        # Store all results in public_ae_data table
        logger.info(f"Storing {len(all_results)} total results in public_ae_data...")
        storage_result = store_public_ae_data(all_results)
        
        logger.info(f"Public storage complete: {storage_result['inserted']} inserted, {storage_result['errors']} errors")
        
        return {
            "success": True,
            "drugs_processed": len(drug_terms),
            "total_results": len(all_results),
            "storage_result": storage_result,
            "source_stats": source_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error during public daily pull: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

