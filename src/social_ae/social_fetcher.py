"""
Social media fetcher for adverse event detection.
Handles API pulls from Reddit, X (Twitter), YouTube, and other platforms.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.utils.config_loader import load_config


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    reraise=True
)
def _fetch_reddit_api_request(url: str, params: dict, timeout: int = 10) -> requests.Response:
    """
    Internal function to make Reddit API request with retry logic.
    
    Args:
        url: API endpoint URL
        params: Request parameters
        timeout: Request timeout in seconds
    
    Returns:
        Response object
    
    Raises:
        requests.exceptions.RequestException: If request fails after retries
    """
    return requests.get(url, params=params, timeout=timeout)


def fetch_reddit_posts(drug_terms: List[str], limit_per_term: int = 50, days_back: int = 7) -> List[Dict]:
    """
    Fetch Reddit posts/comments mentioning drug terms.
    
    Uses Pushshift API (free tier) or Reddit API.
    Falls back to mock data if API unavailable.
    
    Args:
        drug_terms: List of drug names/keywords to search
        limit_per_term: Maximum posts per drug term
        days_back: How many days back to search
    
    Returns:
        List of post dictionaries with source, text, timestamp, etc.
    """
    posts = []
    
    # Calculate time range
    after_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
    
    for term in drug_terms:
        term = term.strip().lower()
        if not term:
            continue
        
        try:
            # Try Pushshift API (free, no auth required)
            url = "https://api.pushshift.io/reddit/search/comment/"
            params = {
                "q": term,
                "size": limit_per_term,
                "after": after_timestamp,
                "sort": "created_utc",
                "sort_type": "desc",
            }
            
            # Use retry-enabled request function
            response = _fetch_reddit_api_request(url, params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    body = item.get("body", "")
                    if body and len(body) > 20:  # Filter very short comments
                        posts.append({
                            "source": "reddit",
                            "platform": "reddit",
                            "text": body,
                            "created_utc": item.get("created_utc"),
                            "post_id": item.get("id"),
                            "subreddit": item.get("subreddit", "unknown"),
                            "author": item.get("author", "[deleted]"),
                            "drug_match": term,
                            "url": f"https://reddit.com{item.get('permalink', '')}",
                            "score": item.get("score", 0),
                        })
            
            # Rate limiting - be respectful
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            # If API fails, continue to next term
            st.warning(f"⚠️ Reddit API error for '{term}': {str(e)[:100]}")
            continue
        except Exception as e:
            st.warning(f"⚠️ Error fetching Reddit data for '{term}': {str(e)[:100]}")
            continue
    
    return posts


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    reraise=True
)
def _fetch_x_api_request(url: str, headers: dict, params: dict, timeout: int = 10) -> requests.Response:
    """
    Internal function to make X API request with retry logic.
    
    Args:
        url: API endpoint URL
        headers: Request headers
        params: Request parameters
        timeout: Request timeout in seconds
    
    Returns:
        Response object
    
    Raises:
        requests.exceptions.RequestException: If request fails after retries
    """
    return requests.get(url, headers=headers, params=params, timeout=timeout)


def fetch_x_posts(drug_terms: List[str], limit_per_term: int = 50) -> List[Dict]:
    """
    Fetch X (Twitter) posts mentioning drug terms.
    
    Note: X API v2 requires authentication. This is a placeholder
    that can be extended with actual API credentials.
    
    Args:
        drug_terms: List of drug names/keywords to search
        limit_per_term: Maximum posts per drug term
    
    Returns:
        List of post dictionaries
    """
    posts = []
    
    # Placeholder: X API requires Bearer token authentication
    # To use: Set X_API_BEARER_TOKEN in environment or session state
    api_token = st.session_state.get("x_api_bearer_token") or st.secrets.get("X_API_BEARER_TOKEN", None)
    
    if not api_token:
        # Return mock data structure for demonstration
        st.info("ℹ️ X API requires authentication. Add X_API_BEARER_TOKEN to use real data.")
        return posts
    
    for term in drug_terms:
        term = term.strip()
        if not term:
            continue
        
        try:
            # X API v2 endpoint
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {api_token}",
            }
            params = {
                "query": f"{term} -is:retweet lang:en",
                "max_results": min(limit_per_term, 100),
                "tweet.fields": "created_at,author_id,public_metrics",
            }
            
            # Use retry-enabled request function
            response = _fetch_x_api_request(url, headers, params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    text = item.get("text", "")
                    if text and len(text) > 10:
                        posts.append({
                            "source": "x",
                            "platform": "twitter",
                            "text": text,
                            "created_utc": None,  # X uses created_at ISO format
                            "post_id": item.get("id"),
                            "author": item.get("author_id", "unknown"),
                            "drug_match": term,
                            "url": f"https://twitter.com/i/web/status/{item.get('id')}",
                            "metrics": item.get("public_metrics", {}),
                        })
            
            time.sleep(1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ X API error for '{term}': {str(e)[:100]}")
            continue
        except Exception as e:
            st.warning(f"⚠️ Error fetching X data for '{term}': {str(e)[:100]}")
            continue
    
    return posts


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    reraise=True
)
def _fetch_youtube_api_request(url: str, params: dict, timeout: int = 10) -> requests.Response:
    """
    Internal function to make YouTube API request with retry logic.
    
    Args:
        url: API endpoint URL
        params: Request parameters
        timeout: Request timeout in seconds
    
    Returns:
        Response object
    
    Raises:
        requests.exceptions.RequestException: If request fails after retries
    """
    return requests.get(url, params=params, timeout=timeout)


def fetch_youtube_comments(drug_terms: List[str], limit_per_term: int = 50, days_back: int = 30) -> List[Dict]:
    """
    Fetch YouTube comments from videos mentioning drug terms.
    
    Uses YouTube Data API v3 to:
    1. Search for videos about the drug
    2. Extract comments from those videos
    3. Filter for potential AE mentions
    
    Args:
        drug_terms: List of drug names/keywords to search
        limit_per_term: Maximum comments per drug term
        days_back: How many days back to search (YouTube API limitation)
    
    Returns:
        List of comment dictionaries with source, text, timestamp, etc.
    """
    posts = []
    
    # Get API key from config or environment
    config = load_config()
    api_key = (
        config.get("api_keys", {}).get("YOUTUBE_API_KEY") or
        st.secrets.get("YOUTUBE_API_KEY", None) or
        st.session_state.get("youtube_api_key", None)
    )
    
    if not api_key:
        st.info("ℹ️ YouTube API requires authentication. Add YOUTUBE_API_KEY to use YouTube data.")
        return posts
    
    # Calculate publishedAfter date (YouTube API uses ISO 8601)
    published_after = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    for term in drug_terms:
        term = term.strip()
        if not term:
            continue
        
        try:
            # Step 1: Search for videos about the drug
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                "part": "snippet",
                "q": f"{term} review experience side effects",
                "type": "video",
                "maxResults": min(limit_per_term // 5, 20),  # Get fewer videos, more comments per video
                "order": "relevance",
                "publishedAfter": published_after,
                "key": api_key,
            }
            
            search_response = _fetch_youtube_api_request(search_url, search_params, timeout=10)
            
            if search_response.status_code != 200:
                error_data = search_response.json() if search_response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                st.warning(f"⚠️ YouTube search API error for '{term}': {error_msg}")
                continue
            
            search_data = search_response.json()
            video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
            
            if not video_ids:
                continue
            
            # Step 2: Get comments from each video
            for video_id in video_ids[:10]:  # Limit to 10 videos per drug term
                try:
                    comments_url = "https://www.googleapis.com/youtube/v3/commentThreads"
                    comments_params = {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": 50,  # Max comments per video
                        "order": "relevance",
                        "textFormat": "plainText",
                        "key": api_key,
                    }
                    
                    comments_response = _fetch_youtube_api_request(comments_url, comments_params, timeout=10)
                    
                    if comments_response.status_code == 200:
                        comments_data = comments_response.json()
                        for item in comments_data.get("items", []):
                            snippet = item.get("snippet", {})
                            top_level = snippet.get("topLevelComment", {}).get("snippet", {})
                            text = top_level.get("textDisplay", "")
                            
                            if text and len(text) > 20:  # Filter very short comments
                                published_at = top_level.get("publishedAt", "")
                                # Convert ISO 8601 to Unix timestamp
                                try:
                                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                                    created_utc = int(dt.timestamp())
                                except:
                                    created_utc = None
                                
                                posts.append({
                                    "source": "youtube",
                                    "platform": "youtube",
                                    "text": text,
                                    "created_utc": created_utc,
                                    "post_id": top_level.get("id"),
                                    "author": top_level.get("authorDisplayName", "unknown"),
                                    "drug_match": term,
                                    "url": f"https://www.youtube.com/watch?v={video_id}&lc={top_level.get('id')}",
                                    "video_id": video_id,
                                    "video_title": search_data.get("items", [{}])[0].get("snippet", {}).get("title", ""),
                                    "like_count": top_level.get("likeCount", 0),
                                })
                    
                    # Rate limiting - YouTube quota: 1 search = 100 units, 1 commentThread = 1 unit
                    time.sleep(0.2)
                    
                except requests.exceptions.RequestException as e:
                    # Continue to next video if one fails
                    continue
                except Exception as e:
                    continue
            
            # Rate limiting between drug terms
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ YouTube API error for '{term}': {str(e)[:100]}")
            continue
        except Exception as e:
            st.warning(f"⚠️ Error fetching YouTube data for '{term}': {str(e)[:100]}")
            continue
    
    return posts


def fetch_daily_social_posts(
    drug_terms: str,
    platforms: List[str] = None,
    limit_per_term: int = 50,
    days_back: int = 7,
) -> List[Dict]:
    """
    Main entry point: Fetch social media posts for given drug terms.
    
    Args:
        drug_terms: Comma-separated drug names/keywords
        platforms: List of platforms to search (["reddit", "x"] or None for all)
        limit_per_term: Max posts per drug term per platform
        days_back: Days back to search
    
    Returns:
        Combined list of posts from all platforms
    """
    if platforms is None:
        platforms = ["reddit"]  # Default to Reddit (no auth required)
    
    terms = [t.strip() for t in drug_terms.split(",") if t.strip()]
    
    if not terms:
        return []
    
    all_posts = []
    
    if "reddit" in platforms:
        reddit_posts = fetch_reddit_posts(terms, limit_per_term, days_back)
        all_posts.extend(reddit_posts)
    
    if "x" in platforms or "twitter" in platforms:
        x_posts = fetch_x_posts(terms, limit_per_term)
        all_posts.extend(x_posts)
    
    if "youtube" in platforms:
        youtube_posts = fetch_youtube_comments(terms, limit_per_term, days_back)
        all_posts.extend(youtube_posts)
    
    # Sort by timestamp (newest first)
    all_posts.sort(
        key=lambda x: x.get("created_utc") or 0,
        reverse=True
    )
    
    return all_posts

