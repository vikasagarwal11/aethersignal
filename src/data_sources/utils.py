"""
Utility functions for data source processing.
Provides normalization, cleaning, and AI scoring helpers.
"""

import re
from typing import Dict, Any, Optional

# Import drug normalization
try:
    import sys
    from pathlib import Path
    # Add src to path if needed
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from drug_name_normalization import normalize_drug_name
except ImportError:
    try:
        from src.drug_name_normalization import normalize_drug_name
    except ImportError:
        # Fallback if module not found
        def normalize_drug_name(drug: str, aggressive: bool = False) -> str:
            if not drug:
                return ""
            return str(drug).strip().lower()


def sanitize_text(text: str) -> str:
    """
    Sanitize and clean text for adverse event processing.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Basic cleaning
    text = str(text).strip()
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Truncate if too long (keep first 5000 chars)
    if len(text) > 5000:
        text = text[:5000] + "..."
    
    return text


def estimate_confidence(text: str) -> float:
    """
    Estimate confidence score for an adverse event based on text.
    Simple rule-based approach (can be enhanced with ML later).
    
    Args:
        text: Text describing the adverse event
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    confidence = 0.5  # Base confidence
    
    # Increase confidence for medical terms
    medical_terms = [
        "adverse", "reaction", "side effect", "symptom",
        "hospital", "doctor", "physician", "medication",
        "prescribed", "diagnosed", "treatment"
    ]
    
    for term in medical_terms:
        if term in text_lower:
            confidence += 0.1
    
    # Increase confidence for specific severity indicators
    severity_indicators = [
        "severe", "serious", "emergency", "er", "icu",
        "hospitalized", "discontinued", "stopped"
    ]
    
    for indicator in severity_indicators:
        if indicator in text_lower:
            confidence += 0.05
    
    # Decrease confidence for uncertain language
    uncertain_terms = [
        "maybe", "might", "possibly", "perhaps",
        "not sure", "think", "believe"
    ]
    
    for term in uncertain_terms:
        if term in text_lower:
            confidence -= 0.1
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))


def estimate_severity(text: str) -> float:
    """
    Estimate severity score for an adverse event based on text.
    Simple rule-based approach (can be enhanced with ML later).
    
    Args:
        text: Text describing the adverse event
        
    Returns:
        Severity score between 0.0 and 1.0
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    severity = 0.0
    
    # High severity indicators
    high_severity = [
        "death", "died", "fatal", "lethal",
        "hospitalized", "icu", "intensive care",
        "emergency", "er visit", "ambulance",
        "life threatening", "life-threatening"
    ]
    
    for indicator in high_severity:
        if indicator in text_lower:
            severity = max(severity, 0.9)
    
    # Medium-high severity
    medium_high = [
        "severe", "serious", "discontinued", "stopped",
        "allergic reaction", "anaphylaxis", "seizure"
    ]
    
    for indicator in medium_high:
        if indicator in text_lower:
            severity = max(severity, 0.7)
    
    # Medium severity
    medium = [
        "moderate", "uncomfortable", "painful",
        "persistent", "ongoing", "chronic"
    ]
    
    for indicator in medium:
        if indicator in text_lower:
            severity = max(severity, 0.5)
    
    # Low severity
    low = [
        "mild", "slight", "minor", "uncomfortable",
        "annoying", "bothersome"
    ]
    
    for indicator in low:
        if indicator in text_lower:
            severity = max(severity, 0.2)
    
    # If no indicators found, default to low
    if severity == 0.0:
        severity = 0.1
    
    return min(1.0, severity)

