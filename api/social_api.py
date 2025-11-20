"""
FastAPI endpoint for Social AE daily pulls.
Deploy to Render, Railway, or EC2.
"""

import os
from datetime import datetime
from typing import Optional
import logging

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Social AE modules
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.social_ae.social_fetcher import fetch_daily_social_posts
from src.social_ae.social_cleaner import clean_and_normalize_posts
from src.social_ae.social_mapper import extract_reactions_from_posts
from src.social_ae.social_anonymizer import anonymize_posts
from src.social_ae.social_storage import store_social_records
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Social AE Ingestion API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PullRequest(BaseModel):
    source: Optional[str] = "api"
    timestamp: Optional[str] = None
    drug_terms: Optional[str] = None
    platforms: Optional[list] = None


# Default drug watchlist
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


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Social AE Ingestion API",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/social/daily")
async def run_daily_social_pull(
    request: Optional[PullRequest] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Run daily Social AE pull and store in Supabase.
    
    Called by Supabase Edge Function on schedule.
    """
    # Optional: Verify API secret key
    api_secret = os.getenv("API_SECRET_KEY")
    if api_secret and authorization != f"Bearer {api_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Get parameters
        drug_terms_str = request.drug_terms if request and request.drug_terms else ", ".join(DEFAULT_DRUG_WATCHLIST)
        platforms = request.platforms if request and request.platforms else ["reddit"]
        
        logger.info(f"Starting daily pull: {len(drug_terms_str.split(','))} drugs, platforms: {platforms}")
        
        # Step 1: Fetch posts
        logger.info("Fetching posts from social media...")
        raw_posts = fetch_daily_social_posts(
            drug_terms_str,
            platforms=platforms,
            limit_per_term=50,
            days_back=1,
        )
        
        if not raw_posts:
            logger.warning("No posts fetched")
            return {
                "success": False,
                "error": "No posts fetched",
                "posts_fetched": 0,
                "inserted": 0
            }
        
        logger.info(f"Fetched {len(raw_posts)} raw posts")
        
        # Step 2: Clean and normalize
        logger.info("Cleaning and normalizing posts...")
        cleaned_df = clean_and_normalize_posts(raw_posts, use_ml=False)  # ML optional for speed
        
        if cleaned_df.empty:
            logger.warning("All posts filtered out during cleaning")
            return {
                "success": False,
                "error": "All posts filtered out",
                "posts_fetched": len(raw_posts),
                "posts_cleaned": 0,
                "inserted": 0
            }
        
        logger.info(f"Cleaned {len(cleaned_df)} posts")
        
        # Step 3: Extract reactions
        logger.info("Extracting reactions...")
        df_with_reactions = extract_reactions_from_posts(cleaned_df, include_confidence=True)
        
        # Step 4: Anonymize
        logger.info("Anonymizing posts...")
        posts_list = df_with_reactions.to_dict('records')
        anonymized_posts = anonymize_posts(posts_list)
        df_final = pd.DataFrame(anonymized_posts)
        
        logger.info(f"Final dataset: {len(df_final)} posts")
        
        # Step 5: Store in Supabase
        logger.info("Storing posts in Supabase...")
        storage_result = store_social_records(df_final)
        
        logger.info(f"Storage complete: {storage_result['inserted']} inserted, {storage_result['errors']} errors")
        
        return {
            "success": True,
            "posts_fetched": len(raw_posts),
            "posts_cleaned": len(cleaned_df),
            "posts_with_reactions": int(df_final["has_reaction"].sum()) if "has_reaction" in df_final.columns else 0,
            "posts_stored": storage_result["inserted"],
            "posts_errors": storage_result["errors"],
            "inserted": storage_result["inserted"],  # Alias for compatibility
            "duplicates": 0,  # Handled by upsert
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during daily pull: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during pull: {str(e)}"
        )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

