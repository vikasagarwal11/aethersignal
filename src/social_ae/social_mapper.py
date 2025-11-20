"""
Social media slang to MedDRA mapping.
Maps informal language to standardized adverse event terms.
"""

import re
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd


# Slang to medical term mapping
SLANG_MAP = {
    # Gastrointestinal
    "puking": "vomiting",
    "threw up": "vomiting",
    "barf": "vomiting",
    "nauseous": "nausea",
    "felt nauseous": "nausea",
    "queasy": "nausea",
    "upset stomach": "abdominal pain",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "diarrhea": "diarrhoea",
    "the runs": "diarrhoea",
    "constipated": "constipation",
    
    # Neurological
    "dizzy": "dizziness",
    "felt dizzy": "dizziness",
    "lightheaded": "dizziness",
    "woozy": "dizziness",
    "headache": "headache",
    "migraine": "migraine",
    "brain fog": "cognitive disorder",
    "can't think straight": "cognitive disorder",
    "confused": "confusional state",
    
    # Cardiovascular
    "heart racing": "tachycardia",
    "fast heartbeat": "tachycardia",
    "palpitations": "palpitations",
    "chest pain": "chest pain",
    "chest tightness": "chest discomfort",
    
    # Dermatological
    "rash": "rash",
    "hives": "urticaria",
    "itchy": "pruritus",
    "red skin": "erythema",
    "swollen": "oedema",
    
    # Musculoskeletal
    "joint pain": "arthralgia",
    "muscle pain": "myalgia",
    "back pain": "back pain",
    "sore muscles": "myalgia",
    
    # Respiratory
    "short of breath": "dyspnoea",
    "can't breathe": "dyspnoea",
    "wheezing": "wheezing",
    "cough": "cough",
    
    # General
    "tired": "fatigue",
    "exhausted": "fatigue",
    "worn out": "fatigue",
    "weak": "asthenia",
    "fever": "pyrexia",
    "chills": "chills",
    "sweating": "sweating",
    "insomnia": "insomnia",
    "can't sleep": "insomnia",
    "anxious": "anxiety",
    "panic": "panic attack",
    "depressed": "depression",
    "mood swings": "mood altered",
}

# Pattern-based mappings (regex patterns)
PATTERN_MAP = [
    (r"\bthrew\s+up\b", "vomiting"),
    (r"\bpuked?\b", "vomiting"),
    (r"\bnauseous?\b", "nausea"),
    (r"\bdizzy\b", "dizziness"),
    (r"\bheadache\b", "headache"),
    (r"\brash\b", "rash"),
    (r"\bitchy\b", "pruritus"),
    (r"\btired\b", "fatigue"),
    (r"\bexhausted\b", "fatigue"),
    (r"\bfever\b", "pyrexia"),
    (r"\bchills\b", "chills"),
    (r"\bjoint\s+pain\b", "arthralgia"),
    (r"\bmuscle\s+pain\b", "myalgia"),
    (r"\bback\s+pain\b", "back pain"),
    (r"\bshort\s+of\s+breath\b", "dyspnoea"),
    (r"\bcan'?t\s+breathe\b", "dyspnoea"),
    (r"\bheart\s+racing\b", "tachycardia"),
    (r"\bfast\s+heartbeat\b", "tachycardia"),
    (r"\bchest\s+pain\b", "chest pain"),
    (r"\banxious\b", "anxiety"),
    (r"\bpanic\b", "panic attack"),
    (r"\bdepressed\b", "depression"),
    (r"\binsomnia\b", "insomnia"),
    (r"\bcan'?t\s+sleep\b", "insomnia"),
]


def map_slang_to_reaction(text: str, return_confidence: bool = False) -> Union[Tuple[Optional[str], float], Optional[str]]:
    """
    Map informal language in text to standardized reaction term.
    
    Args:
        text: Social media post text
        return_confidence: If True, returns (reaction, confidence_score) tuple
    
    Returns:
        Standardized reaction term or (reaction, confidence) tuple
        Confidence score: 0.0-1.0 (1.0 = high confidence, 0.6 = medium, 0.3 = low)
    """
    if not text or not isinstance(text, str):
        return (None, 0.0) if return_confidence else None
    
    text_lower = text.lower()
    confidence = 0.0
    reaction = None
    
    # First check exact slang matches (highest confidence)
    for slang, mapped_reaction in SLANG_MAP.items():
        if slang in text_lower:
            # Exact match = high confidence
            reaction = mapped_reaction
            confidence = 0.9
            break
    
    # Then check pattern matches (medium confidence)
    if not reaction:
        for pattern, mapped_reaction in PATTERN_MAP:
            if re.search(pattern, text_lower, re.IGNORECASE):
                reaction = mapped_reaction
                confidence = 0.7  # Pattern match = medium confidence
                break
    
    # Boost confidence if drug mention present (context indicator)
    if reaction:
        # Check for common drug mention patterns
        drug_indicators = [
            r'\b(took|taking|on|using|started|stopped)\s+\w+',  # "took ozempic"
            r'\b(drug|medication|medicine|prescription)\b',
        ]
        has_drug_context = any(re.search(indicator, text_lower) for indicator in drug_indicators)
        if has_drug_context:
            confidence = min(1.0, confidence + 0.1)  # Boost by 0.1
    
    # Reduce confidence if negation detected
    if reaction:
        negation_patterns = [
            r'\b(no|not|never|didn\'t|doesn\'t|won\'t|isn\'t)\s+\w+\s+(vomiting|nausea|dizzy|rash|pain)',
            r'\b(without|lack of|absence of)\s+\w+',
        ]
        has_negation = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in negation_patterns)
        if has_negation:
            confidence = max(0.2, confidence - 0.3)  # Reduce significantly
    
    if return_confidence:
        return (reaction, confidence)
    return reaction


def extract_reactions_from_posts(df: pd.DataFrame, include_confidence: bool = True) -> pd.DataFrame:
    """
    Extract and map reactions from social media posts.
    
    Args:
        df: DataFrame with cleaned posts (from social_cleaner)
        include_confidence: If True, adds confidence_score column
    
    Returns:
        DataFrame with added 'reaction' and optionally 'confidence_score' columns
    """
    if df.empty or "text" not in df.columns:
        return df
    
    reactions = []
    confidence_scores = []
    
    for text in df["text"]:
        result = map_slang_to_reaction(str(text), return_confidence=include_confidence)
        if include_confidence:
            reaction, confidence = result if result else (None, 0.0)
            reactions.append(reaction)
            confidence_scores.append(confidence)
        else:
            reactions.append(result)
    
    df["reaction"] = reactions
    
    if include_confidence:
        df["confidence_score"] = confidence_scores
    
    # Also add a flag for posts with detected reactions
    df["has_reaction"] = df["reaction"].notna()
    
    # Add confidence category for easy filtering
    if include_confidence:
        df["confidence_level"] = df["confidence_score"].apply(
            lambda x: "High" if x >= 0.8 else "Medium" if x >= 0.5 else "Low" if x > 0 else "None"
        )
    
    return df


def get_reaction_summary(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get summary of detected reactions.
    
    Args:
        df: DataFrame with reactions mapped
    
    Returns:
        Dictionary mapping reaction terms to counts
    """
    if df.empty or "reaction" not in df.columns:
        return {}
    
    reaction_counts = df["reaction"].value_counts().to_dict()
    return reaction_counts


def normalize_to_meddra(reaction: str) -> Optional[str]:
    """
    Normalize reaction term to MedDRA Preferred Term (PT).
    
    This is a placeholder - in production, you'd use:
    - MedDRA API
    - UMLS mapping
    - Custom dictionary
    
    Args:
        reaction: Standardized reaction term
    
    Returns:
        MedDRA PT or original term if not found
    """
    if not reaction:
        return None
    
    # Placeholder mapping (in production, use MedDRA API)
    meddra_mapping = {
        "vomiting": "Vomiting",
        "nausea": "Nausea",
        "diarrhoea": "Diarrhoea",
        "constipation": "Constipation",
        "dizziness": "Dizziness",
        "headache": "Headache",
        "rash": "Rash",
        "pruritus": "Pruritus",
        "fatigue": "Fatigue",
        "pyrexia": "Pyrexia",
        "arthralgia": "Arthralgia",
        "myalgia": "Myalgia",
        "dyspnoea": "Dyspnoea",
        "tachycardia": "Tachycardia",
        "chest pain": "Chest pain",
        "anxiety": "Anxiety",
        "depression": "Depression",
        "insomnia": "Insomnia",
    }
    
    return meddra_mapping.get(reaction.lower(), reaction)

