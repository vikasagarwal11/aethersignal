"""
Daily automation scheduler for Social AE pulls.
Handles scheduled daily pulls with default drug watchlist.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

import pandas as pd

from .social_fetcher import fetch_daily_social_posts
from .social_cleaner import clean_and_normalize_posts
from .social_mapper import extract_reactions_from_posts
from .social_anonymizer import anonymize_posts
from .social_ae_storage import store_posts, init_database, get_statistics
from src.storage.public_data_storage import store_from_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Default drug watchlist (GLP-1s, high-volume drugs)
DEFAULT_DRUG_WATCHLIST = [
    "ozempic", "wegovy", "mounjaro", "semaglutide", "tirzepatide", 
    "rybelsus", "trulicity", "saxenda", "victoza",
    "adderall", "vyvanse", "ritalin", "concerta",
    "prozac", "zoloft", "lexapro", "cymbalta", "effexor",
    "finasteride", "propecia", "dutasteride",
    "spironolactone", "accutane", "roaccutane",
    "nuvaring", "yaz", "yasmin",
    "lithium", "depakote", "lamictal",
    "humira", "enbrel", "remicade", "stelara",
    "keytruda", "opdivo", "imfinzi"
]


def run_daily_pull(
    drug_terms: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    days_back: int = 1,
    limit_per_term: int = 50,
    anonymize: bool = True
) -> Dict:
    """
    Run a daily pull of social media posts.
    
    Args:
        drug_terms: List of drug terms (defaults to watchlist)
        platforms: List of platforms (defaults to ["reddit"])
        days_back: Days back to search
        limit_per_term: Max posts per drug term
        anonymize: Whether to anonymize posts
    
    Returns:
        Dictionary with pull results and statistics
    """
    if drug_terms is None:
        drug_terms = DEFAULT_DRUG_WATCHLIST
    
    if platforms is None:
        platforms = ["reddit"]  # Default to Reddit (no auth needed)
    
    drug_terms_str = ", ".join(drug_terms)
    
    logger.info(f"Starting daily pull for {len(drug_terms)} drugs on {platforms}")
    
    try:
        # Step 1: Fetch posts
        logger.info("Fetching posts from social media...")
        raw_posts = fetch_daily_social_posts(
            drug_terms_str,
            platforms=platforms,
            limit_per_term=limit_per_term,
            days_back=days_back,
        )
        
        if not raw_posts:
            logger.warning("No posts fetched")
            return {
                "success": False,
                "error": "No posts fetched",
                "posts_fetched": 0
            }
        
        logger.info(f"Fetched {len(raw_posts)} raw posts")
        
        # Step 2: Clean and normalize
        logger.info("Cleaning and normalizing posts...")
        cleaned_df = clean_and_normalize_posts(raw_posts)
        
        if cleaned_df.empty:
            logger.warning("All posts filtered out during cleaning")
            return {
                "success": False,
                "error": "All posts filtered out",
                "posts_fetched": len(raw_posts),
                "posts_cleaned": 0
            }
        
        logger.info(f"Cleaned {len(cleaned_df)} posts")
        
        # Step 3: Extract reactions
        logger.info("Extracting reactions...")
        df_with_reactions = extract_reactions_from_posts(cleaned_df, include_confidence=True)
        
        # Step 4: Anonymize (if enabled)
        if anonymize:
            logger.info("Anonymizing posts...")
            posts_list = df_with_reactions.to_dict('records')
            anonymized_posts = anonymize_posts(posts_list)
            df_final = pd.DataFrame(anonymized_posts)
        else:
            df_final = df_with_reactions
        
        logger.info(f"Final dataset: {len(df_final)} posts")
        
        # Step 5: Store in database
        logger.info("Storing posts in database...")
        posts_list = df_final.to_dict('records')
        storage_result = store_posts(posts_list, drug_terms_str, platforms)
        
        logger.info(f"Storage complete: {storage_result['stored']} new, {storage_result['duplicates']} duplicates")
        
        # Step 6: Also store in public_ae_data table (public data platform)
        logger.info("Storing in public_ae_data table...")
        try:
            # Prepare DataFrame for public storage
            public_df = df_final.copy()
            public_df["source"] = public_df.get("platform", "reddit")
            public_df["drug"] = public_df.get("drug_match", public_df.get("drug_name", ""))
            public_df["reaction"] = public_df.get("reaction", "")
            public_df["text"] = public_df.get("cleaned_text", public_df.get("text", ""))
            public_df["timestamp"] = pd.to_datetime(public_df.get("created_date", datetime.now()))
            public_df["confidence"] = public_df.get("ae_prob", public_df.get("confidence_score", 0.5))
            public_df["severity"] = public_df.get("severity_score", 0.0)
            public_df["metadata"] = public_df.apply(lambda x: {
                "platform": x.get("platform", "reddit"),
                "subreddit": x.get("subreddit", ""),
                "score": int(x.get("score", 0))
            }, axis=1)
            
            public_storage_result = store_from_dataframe(public_df)
            logger.info(f"Public storage: {public_storage_result['inserted']} inserted, {public_storage_result['errors']} errors")
        except Exception as e:
            logger.warning(f"Error storing to public_ae_data: {str(e)}")
            public_storage_result = {"inserted": 0, "errors": 0}
        
        return {
            "success": True,
            "posts_fetched": len(raw_posts),
            "posts_cleaned": len(cleaned_df),
            "posts_with_reactions": int(df_final["has_reaction"].sum()) if "has_reaction" in df_final.columns else 0,
            "posts_stored": storage_result["stored"],
            "posts_duplicate": storage_result["duplicates"],
            "posts_errors": storage_result["errors"],
            "public_data_inserted": public_storage_result.get("inserted", 0),
            "public_data_errors": public_storage_result.get("errors", 0),
            "drug_terms": drug_terms,
            "platforms": platforms,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during daily pull: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def run_scheduled_pull():
    """
    Entry point for scheduled/cron jobs.
    Can be called from cron, GitHub Actions, or APScheduler.
    """
    logger.info("=" * 50)
    logger.info("Starting scheduled Social AE pull")
    logger.info("=" * 50)
    
    result = run_daily_pull(
        drug_terms=None,  # Use default watchlist
        platforms=["reddit"],  # Start with Reddit only
        days_back=1,
        limit_per_term=50,
        anonymize=True
    )
    
    if result["success"]:
        logger.info("Scheduled pull completed successfully")
        logger.info(f"Stored {result['posts_stored']} new posts")
    else:
        logger.error(f"Scheduled pull failed: {result.get('error', 'Unknown error')}")
    
    logger.info("=" * 50)
    
    return result


if __name__ == "__main__":
    # Can be run directly for testing
    result = run_scheduled_pull()
    print(result)


# Public data platform daily pull (includes all free sources)
def run_public_platform_pull() -> Dict:
    """
    Run daily pull for public data platform (all free sources).
    This is the main entry point for GitHub Actions / Cron.
    """
    try:
        from src.data_sources.public_daily_pull import run_public_daily_pull
        
        logger.info("=" * 50)
        logger.info("Starting PUBLIC DATA PLATFORM daily pull")
        logger.info("=" * 50)
        
        result = run_public_daily_pull(
            drug_terms=None,  # Use default watchlist
            days_back=1,
            limit_per_drug=100
        )
        
        if result["success"]:
            logger.info("Public platform pull completed successfully")
            logger.info(f"Total results: {result['total_results']}")
            logger.info(f"Storage: {result['storage_result']['inserted']} inserted")
        else:
            logger.error(f"Public platform pull failed: {result.get('error', 'Unknown error')}")
        
        logger.info("=" * 50)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in public platform pull: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

