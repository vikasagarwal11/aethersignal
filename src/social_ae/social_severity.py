"""
Severity scoring module for Social AE posts.
Adapts FAERS severity rules to social media language patterns.
"""

import re
import pandas as pd
from typing import Dict, Optional, List, Tuple


# Severity keyword mappings
SEVERITY_KEYWORDS = {
    # High severity indicators (+0.5)
    "hospital": 0.5,
    "er": 0.5,
    "emergency room": 0.5,
    "emergency": 0.5,
    "ambulance": 0.5,
    "icu": 0.5,
    "intensive care": 0.5,
    "admitted": 0.5,
    "hospitalized": 0.5,
    "life threatening": 0.5,
    "life-threatening": 0.5,
    "almost died": 0.5,
    "could have died": 0.5,
    "nearly died": 0.5,
    
    # Medium-high severity indicators (+0.3)
    "terrible": 0.3,
    "severe": 0.3,
    "worst": 0.3,
    "awful": 0.3,
    "horrible": 0.3,
    "extreme": 0.3,
    "unbearable": 0.3,
    "intense": 0.3,
    "debilitating": 0.3,
    "couldn't function": 0.3,
    "couldn't work": 0.3,
    "missed work": 0.3,
    "bedridden": 0.3,
    "couldn't get out of bed": 0.3,
    
    # Medium severity indicators (+0.2)
    "bad": 0.2,
    "really bad": 0.2,
    "pretty bad": 0.2,
    "quite bad": 0.2,
    "significant": 0.2,
    "serious": 0.2,
    "concerning": 0.2,
    "worried": 0.2,
    "scared": 0.2,
    "frightened": 0.2,
    
    # Low severity indicators (-0.2)
    "mild": -0.2,
    "slight": -0.2,
    "minor": -0.2,
    "barely": -0.2,
    "a little": -0.2,
    "slightly": -0.2,
    "not too bad": -0.2,
    "manageable": -0.2,
    "tolerable": -0.2,
}

# Outcome keywords (additional severity boost)
OUTCOME_KEYWORDS = {
    "death": 0.5,
    "died": 0.5,
    "fatal": 0.5,
    "deceased": 0.5,
    "passed away": 0.5,
    "disability": 0.3,
    "disabled": 0.3,
    "permanent": 0.3,
    "permanent damage": 0.3,
    "long term": 0.2,
    "long-term": 0.2,
    "chronic": 0.2,
    "ongoing": 0.2,
    "still having": 0.2,
    "hasn't gone away": 0.2,
}

# Duration keywords (longer = potentially more severe)
DURATION_KEYWORDS = {
    "weeks": 0.1,
    "months": 0.2,
    "years": 0.3,
    "still": 0.2,
    "ongoing": 0.2,
    "persistent": 0.2,
    "chronic": 0.2,
}


def calculate_severity_score(text: str, reactions: Optional[List[str]] = None) -> float:
    """
    Calculate severity score for a social media post.
    
    Args:
        text: Post text content
        reactions: List of detected reactions (optional, for context)
    
    Returns:
        Severity score between 0.0 and 1.0
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text_lower = text.lower()
    score = 0.0
    
    # 1. Check for severity keywords
    for keyword, boost in SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            # Check if negated
            if _is_negated_severity(text_lower, keyword):
                continue
            score += boost
    
    # 2. Check for outcome keywords
    for keyword, boost in OUTCOME_KEYWORDS.items():
        if keyword in text_lower:
            if _is_negated_severity(text_lower, keyword):
                continue
            score += boost
    
    # 3. Check for duration indicators (longer duration = potentially more severe)
    for keyword, boost in DURATION_KEYWORDS.items():
        if keyword in text_lower:
            score += boost
    
    # 4. Check for explicit severity mentions
    severity_patterns = [
        (r'\b(severity|severity level|how bad|how severe)\s*(was|is|were|are)?\s*(very|extremely|really)?', 0.2),
        (r'\b(rate|rate it|rate this)\s*(as|at)?\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)', 0.1),
    ]
    
    for pattern, boost in severity_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            score += boost
    
    # 5. Check for reaction-specific severity indicators
    if reactions:
        # Some reactions are inherently more severe
        high_severity_reactions = [
            "seizure", "anaphylaxis", "cardiac arrest", "stroke", "coma",
            "liver failure", "kidney failure", "respiratory failure",
            "suicidal ideation", "psychosis", "hallucinations"
        ]
        
        for reaction in reactions:
            if any(severe_term in reaction.lower() for severe_term in high_severity_reactions):
                score += 0.3
    
    # 6. Check for frequency indicators (more frequent = potentially more severe)
    frequency_patterns = [
        (r'\b(constant|constantly|all the time|non-stop|nonstop|24/7)\b', 0.2),
        (r'\b(every day|daily|multiple times|several times)\b', 0.1),
        (r'\b(once|twice|occasionally|sometimes|rarely)\b', -0.1),
    ]
    
    for pattern, boost in frequency_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            score += boost
    
    # 7. Check for impact on daily life
    impact_patterns = [
        (r'\b(couldn\'t|can\'t|cannot)\s+(work|function|drive|sleep|eat|move|walk|stand)', 0.2),
        (r'\b(had to|need to|needed to)\s+(stop|quit|discontinue|go to|see|visit)', 0.2),
        (r'\b(stopped|quit|discontinued|had to stop)\s+(taking|using)', 0.2),
    ]
    
    for pattern, boost in impact_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            score += boost
    
    # Clamp score between 0.0 and 1.0
    return min(1.0, max(0.0, score))


def _is_negated_severity(text: str, keyword: str) -> bool:
    """
    Check if a severity keyword is negated in the text.
    
    Args:
        text: Lowercase text
        keyword: Keyword to check for negation
    
    Returns:
        True if keyword appears to be negated
    """
    keyword_pos = text.find(keyword)
    if keyword_pos == -1:
        return False
    
    # Check for negation words before the keyword
    before_text = text[max(0, keyword_pos - 50):keyword_pos]
    negation_patterns = [
        r'\b(no|not|never|didn\'t|doesn\'t|wasn\'t|weren\'t|isn\'t)\s+\w*\s*$',
        r'\b(without|lack of|absence of)\s+',
    ]
    
    for pattern in negation_patterns:
        if re.search(pattern, before_text, re.IGNORECASE):
            return True
    
    return False


def classify_severity(score: float) -> str:
    """
    Classify severity score into category.
    
    Args:
        score: Severity score (0.0-1.0)
    
    Returns:
        Severity category: "Low", "Medium", "High", or "Critical"
    """
    if score >= 0.7:
        return "Critical"
    elif score >= 0.5:
        return "High"
    elif score >= 0.3:
        return "Medium"
    elif score > 0.0:
        return "Low"
    else:
        return "None"


def classify_severity_from_text(text: str) -> str:
    """
    Classify severity from text directly (for use in extraction engine).
    
    Args:
        text: Text to analyze
    
    Returns:
        Severity label: "severe", "moderate", "mild", or "unknown"
    """
    if not text or not isinstance(text, str):
        return "unknown"
    
    txt = text.lower()
    
    # Severe indicators
    severe_terms = [
        "hospital", "er", "emergency", "icu", "intensive care",
        "life threatening", "life-threatening", "almost died",
        "could have died", "nearly died", "terrible", "worst",
        "can't function", "can't work", "bedridden"
    ]
    
    for term in severe_terms:
        if term in txt:
            # Check for negation
            if not _is_negated_severity(txt, term):
                return "severe"
    
    # Moderate indicators
    moderate_terms = [
        "moderate", "bad", "pretty bad", "strong", "significant",
        "serious", "concerning"
    ]
    
    for term in moderate_terms:
        if term in txt:
            if not _is_negated_severity(txt, term):
                return "moderate"
    
    # Mild indicators
    mild_terms = [
        "mild", "slight", "light", "little bit", "small",
        "barely", "a little", "slightly", "not too bad"
    ]
    
    for term in mild_terms:
        if term in txt:
            return "mild"
    
    return "unknown"


def severity_score_from_label(severity_label: str) -> float:
    """
    Convert severity label to numeric score (0-1).
    
    Args:
        severity_label: Severity label ("severe", "moderate", "mild", "unknown")
    
    Returns:
        Numeric severity score (0.0-1.0)
    """
    mapping = {
        "severe": 1.0,
        "moderate": 0.6,
        "mild": 0.3,
        "unknown": 0.1,
        # Also handle old classification system
        "Critical": 1.0,
        "High": 0.7,
        "Medium": 0.4,
        "Low": 0.2,
        "None": 0.0
    }
    return mapping.get(severity_label, 0.1)


def calculate_severity_for_posts(df: pd.DataFrame, reactions_col: str = "reactions") -> pd.DataFrame:
    """
    Calculate severity scores for all posts in a DataFrame.
    
    Args:
        df: DataFrame with posts
        reactions_col: Column name containing reactions (list or string)
    
    Returns:
        DataFrame with added 'severity_score' and 'severity_category' columns
    """
    if df.empty or "text" not in df.columns:
        return df
    
    severity_scores = []
    severity_categories = []
    
    for idx, row in df.iterrows():
        text = str(row.get("text", ""))
        reactions = None
        
        if reactions_col in df.columns:
            reactions_val = row.get(reactions_col)
            if isinstance(reactions_val, list):
                reactions = reactions_val
            elif pd.notna(reactions_val):
                # Try to parse if it's a string
                reactions = [r.strip() for r in str(reactions_val).split(",")]
        
        score = calculate_severity_score(text, reactions)
        severity_scores.append(score)
        severity_categories.append(classify_severity(score))
    
    df = df.copy()
    df["severity_score"] = severity_scores
    df["severity_category"] = severity_categories
    
    return df

