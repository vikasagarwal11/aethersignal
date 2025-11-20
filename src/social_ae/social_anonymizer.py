"""
Anonymization module for Social AE posts.
Removes PII and anonymizes user data for HIPAA compliance.
"""

import re
import hashlib
from typing import Dict, List
import pandas as pd


# PII patterns to detect and remove
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
SSN_PATTERN = r'\b\d{3}-?\d{2}-?\d{4}\b'
CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'

# Location patterns (cities, addresses)
ADDRESS_PATTERN = r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b'
ZIP_CODE_PATTERN = r'\b\d{5}(?:-\d{4})?\b'

# Username mentions (e.g., @username, u/username)
USERNAME_MENTION_PATTERN = r'@\w+|u/\w+|/u/\w+'

# Medical record numbers, patient IDs
MEDICAL_ID_PATTERN = r'\b(?:MRN|Patient ID|Case #?)\s*:?\s*\d+\b'


def hash_username(username: str) -> str:
    """Hash username for anonymization."""
    if not username or username in ["[deleted]", "unknown", "[removed]"]:
        return "[anonymous]"
    # Use SHA256 and take first 16 chars for consistent hashing
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def remove_email(text: str) -> tuple[str, bool]:
    """Remove email addresses from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(EMAIL_PATTERN, "[email_removed]", text, flags=re.IGNORECASE)
    return text, text != original


def remove_phone(text: str) -> tuple[str, bool]:
    """Remove phone numbers from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(PHONE_PATTERN, "[phone_removed]", text)
    return text, original != text


def remove_ssn(text: str) -> tuple[str, bool]:
    """Remove SSN from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(SSN_PATTERN, "[ssn_removed]", text)
    return text, original != text


def remove_credit_card(text: str) -> tuple[str, bool]:
    """Remove credit card numbers from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(CREDIT_CARD_PATTERN, "[card_removed]", text)
    return text, original != text


def remove_addresses(text: str) -> tuple[str, bool]:
    """Remove street addresses from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(ADDRESS_PATTERN, "[address_removed]", text, flags=re.IGNORECASE)
    return text, original != text


def remove_zip_codes(text: str) -> tuple[str, bool]:
    """Remove ZIP codes from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(ZIP_CODE_PATTERN, "[zip_removed]", text)
    return text, original != text


def remove_username_mentions(text: str) -> tuple[str, bool]:
    """Remove username mentions (@username, u/username) from text."""
    if not text:
        return text, False
    original = text
    text = re.sub(USERNAME_MENTION_PATTERN, "[user_mention_removed]", text)
    return text, original != text


def remove_medical_ids(text: str) -> tuple[str, bool]:
    """Remove medical record numbers and patient IDs."""
    if not text:
        return text, False
    original = text
    text = re.sub(MEDICAL_ID_PATTERN, "[medical_id_removed]", text, flags=re.IGNORECASE)
    return text, original != text


def anonymize_text(text: str, aggressive: bool = True) -> tuple[str, Dict]:
    """
    Anonymize text by removing PII.
    
    Args:
        text: Original text
        aggressive: If True, also removes usernames and locations
    
    Returns:
        Tuple of (anonymized_text, removal_stats)
    """
    if not text:
        return text, {}
    
    anonymized = text
    stats = {
        "emails_removed": 0,
        "phones_removed": 0,
        "ssns_removed": 0,
        "cards_removed": 0,
        "addresses_removed": 0,
        "zips_removed": 0,
        "usernames_removed": 0,
        "medical_ids_removed": 0,
    }
    
    # Remove emails
    anonymized, removed = remove_email(anonymized)
    if removed:
        stats["emails_removed"] = len(re.findall(EMAIL_PATTERN, text, re.IGNORECASE))
    
    # Remove phone numbers
    anonymized, removed = remove_phone(anonymized)
    if removed:
        stats["phones_removed"] = len(re.findall(PHONE_PATTERN, text))
    
    # Remove SSNs
    anonymized, removed = remove_ssn(anonymized)
    if removed:
        stats["ssns_removed"] = len(re.findall(SSN_PATTERN, text))
    
    # Remove credit cards
    anonymized, removed = remove_credit_card(anonymized)
    if removed:
        stats["cards_removed"] = len(re.findall(CREDIT_CARD_PATTERN, text))
    
    # Aggressive anonymization (for public use)
    if aggressive:
        # Remove addresses
        anonymized, removed = remove_addresses(anonymized)
        if removed:
            stats["addresses_removed"] = len(re.findall(ADDRESS_PATTERN, text, re.IGNORECASE))
        
        # Remove ZIP codes
        anonymized, removed = remove_zip_codes(anonymized)
        if removed:
            stats["zips_removed"] = len(re.findall(ZIP_CODE_PATTERN, text))
        
        # Remove username mentions
        anonymized, removed = remove_username_mentions(anonymized)
        if removed:
            stats["usernames_removed"] = len(re.findall(USERNAME_MENTION_PATTERN, text))
    
    # Remove medical IDs
    anonymized, removed = remove_medical_ids(anonymized)
    if removed:
        stats["medical_ids_removed"] = len(re.findall(MEDICAL_ID_PATTERN, text, re.IGNORECASE))
    
    return anonymized, stats


def anonymize_posts(posts: List[Dict]) -> List[Dict]:
    """
    Anonymize a list of posts.
    
    Args:
        posts: List of post dictionaries
    
    Returns:
        List of anonymized posts with is_anonymized flag
    """
    anonymized_posts = []
    
    for post in posts:
        anonymized_post = post.copy()
        
        # Anonymize text
        original_text = post.get("text", post.get("raw_text", ""))
        anonymized_text, removal_stats = anonymize_text(original_text, aggressive=True)
        
        anonymized_post["raw_text"] = original_text  # Keep original for reference
        anonymized_post["text"] = anonymized_text
        anonymized_post["cleaned_text"] = anonymized_text  # Update cleaned text too
        
        # Hash username/author
        author = post.get("author", post.get("username", ""))
        anonymized_post["author"] = hash_username(author)
        anonymized_post["author_hash"] = hash_username(author)
        
        # Mark as anonymized
        anonymized_post["is_anonymized"] = True
        anonymized_post["anonymization_stats"] = removal_stats
        
        anonymized_posts.append(anonymized_post)
    
    return anonymized_posts


def anonymize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Anonymize a DataFrame of posts.
    
    Args:
        df: DataFrame with posts
    
    Returns:
        Anonymized DataFrame
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Anonymize text columns
    text_columns = ["text", "raw_text", "cleaned_text"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: anonymize_text(str(x) if pd.notnull(x) else "", aggressive=True)[0]
            )
    
    # Hash author/usernames
    author_columns = ["author", "username"]
    for col in author_columns:
        if col in df.columns:
            df[col] = df[col].apply(hash_username)
    
    # Add anonymization flag
    df["is_anonymized"] = True
    
    return df

