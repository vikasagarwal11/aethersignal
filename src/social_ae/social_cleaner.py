"""
Social media post cleaner for adverse event detection.
Removes noise, spam, and non-relevant content using rule-based filters.
"""

import re
from typing import List, Dict
import pandas as pd


# Common spam patterns
SPAM_PATTERNS = [
    r"buy\s+(now|here|online|cheap)",
    r"click\s+(here|link|now)",
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
    r"discount|promo|sale|offer",
    r"dm\s+me|message\s+me|contact\s+me",
    r"follow\s+@\w+",
    r"rt\s+@|retweet",
]

# Low-quality content indicators
LOW_QUALITY_INDICATORS = [
    r"^[a-z]{1,3}$",  # Very short words only
    r"^\d+$",  # Numbers only
    r"^[^\w\s]+$",  # Only symbols
]

# Minimum/maximum length thresholds
MIN_LENGTH = 20
MAX_LENGTH = 2000


def is_spam(text: str) -> bool:
    """Check if text matches spam patterns."""
    if not text or not isinstance(text, str):
        return True
    
    text_lower = text.lower()
    
    # Check spam patterns
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Check low-quality indicators
    for pattern in LOW_QUALITY_INDICATORS:
        if re.match(pattern, text.strip()):
            return True
    
    return False


def is_too_short_or_long(text: str) -> bool:
    """Check if text is outside acceptable length range."""
    if not text:
        return True
    
    length = len(text.strip())
    return length < MIN_LENGTH or length > MAX_LENGTH


def has_minimal_substance(text: str) -> bool:
    """Check if text has minimal substantive content (too many emojis, etc.)."""
    if not text:
        return True
    
    # Count words vs emojis/symbols
    words = len(re.findall(r'\b\w+\b', text))
    symbols = len(re.findall(r'[^\w\s]', text))
    
    # If mostly symbols, likely low quality
    if words > 0 and symbols / (words + symbols) > 0.5:
        return True
    
    # Need at least 3 words for substance
    if words < 3:
        return True
    
    return False


def clean_text(text: str) -> str:
    """Basic text cleaning: normalize whitespace, remove excessive newlines."""
    if not text:
        return ""
    
    # Remove excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize whitespace
    text = re.sub(r' +', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_and_normalize_posts(posts: List[Dict], use_ml: bool = False) -> pd.DataFrame:
    """
    Clean and normalize social media posts.
    
    Removes spam, low-quality content, and normalizes text.
    
    Args:
        posts: List of post dictionaries from social_fetcher
    
    Returns:
        DataFrame with cleaned posts and quality flags
    """
    if not posts:
        return pd.DataFrame()
    
    cleaned = []
    
    for post in posts:
        text = post.get("text", "")
        
        # Skip if missing text
        if not text:
            continue
        
        # Clean text
        cleaned_text = clean_text(text)
        
        # Quality checks
        is_spam_flag = is_spam(cleaned_text)
        is_too_short = is_too_short_or_long(cleaned_text)
        low_substance = has_minimal_substance(cleaned_text)
        
        # Skip if fails quality checks
        if is_spam_flag or is_too_short or low_substance:
            continue
        
        # Build cleaned post record
        cleaned_post = {
            "source": post.get("source", "unknown"),
            "platform": post.get("platform", "unknown"),
            "text": cleaned_text,
            "original_text": text[:500],  # Keep original for reference
            "created_utc": post.get("created_utc"),
            "post_id": post.get("post_id", ""),
            "subreddit": post.get("subreddit", ""),
            "author": post.get("author", ""),
            "drug_match": post.get("drug_match", ""),
            "url": post.get("url", ""),
            "score": post.get("score", 0),
            "text_length": len(cleaned_text),
            "word_count": len(re.findall(r'\b\w+\b', cleaned_text)),
        }
        
        cleaned.append(cleaned_post)
    
    if not cleaned:
        return pd.DataFrame()
    
    df = pd.DataFrame(cleaned)
    
    # Convert timestamp to datetime if available
    if "created_utc" in df.columns:
        df["created_date"] = pd.to_datetime(
            df["created_utc"], unit="s", errors="coerce"
        )
    
    # Sort by timestamp (newest first)
    if "created_date" in df.columns:
        df = df.sort_values("created_date", ascending=False, na_position="last")
    
    # Enhance with ML if requested
    if use_ml:
        try:
            from .ml_classifier import enhance_with_ml
            df = enhance_with_ml(df, text_column="text")
        except Exception:
            # If ML fails, continue without it
            df["ae_prob"] = 0.0
            df["ml_available"] = False
    
    return df

