"""
Reaction Dictionary - Free MedDRA-like mapping.
Provides Preferred Terms (PT), synonyms, categories, and patterns.
REUSES existing FREE_MEDDRA_LIKE from utils.py and extends it.
"""

from typing import Dict, List, Optional
import re

# Import existing MedDRA mapping from utils
try:
    from src.utils import FREE_MEDDRA_LIKE, map_to_meddra_pt
except ImportError:
    # Fallback if utils not available
    FREE_MEDDRA_LIKE = {}
    def map_to_meddra_pt(term: str) -> str:
        return term.title() if term else ""

# Import existing emoji map from social_mapper
try:
    from src.social_ae.social_mapper import EMOJI_AE_MAP
except ImportError:
    EMOJI_AE_MAP = {}

# SOC-like categories (System Organ Class)
REACTION_CATEGORIES = {
    "Gastrointestinal": [
        "nausea", "vomiting", "diarrhea", "diarrhoea", "constipation",
        "abdominal pain", "dyspepsia", "gastrointestinal disorder"
    ],
    "Neurological": [
        "headache", "migraine", "dizziness", "vertigo", "cognitive disorder",
        "confusional state", "seizure", "tremor"
    ],
    "Cardiovascular": [
        "palpitations", "tachycardia", "chest pain", "chest discomfort",
        "hypertension", "hypotension", "cardiac disorder"
    ],
    "Dermatological": [
        "rash", "urticaria", "pruritus", "erythema", "oedema",
        "injection site reaction", "injection site pain"
    ],
    "Musculoskeletal": [
        "arthralgia", "myalgia", "back pain", "musculoskeletal stiffness",
        "muscle spasms", "asthenia"
    ],
    "Respiratory": [
        "dyspnoea", "cough", "wheezing", "nasal congestion", "rhinorrhoea",
        "pharyngolaryngeal pain", "dysphonia", "respiratory disorder"
    ],
    "Psychiatric": [
        "anxiety", "panic attack", "depression", "irritability", "mood altered",
        "suicidal ideation", "mania", "agitation", "restlessness"
    ],
    "General": [
        "fatigue", "lethargy", "pyrexia", "chills", "hot flush",
        "sweating", "hyperhidrosis", "polydipsia", "pollakiuria"
    ],
    "Endocrine": [
        "hot flush", "sweating", "chills", "polydipsia", "pollakiuria"
    ],
    "Ocular": [
        "vision blurred", "diplopia", "eye pain", "dry eye",
        "lacrimation increased", "photophobia", "eye irritation"
    ],
    "Other": []
}

# Extended reaction dictionary with PT, synonyms, patterns, emoji, category
REACTION_DICTIONARY: Dict[str, Dict] = {}

# Build dictionary from existing FREE_MEDDRA_LIKE
for synonym, pt in FREE_MEDDRA_LIKE.items():
    if pt not in REACTION_DICTIONARY:
        # Find category
        category = "Other"
        for cat, terms in REACTION_CATEGORIES.items():
            if pt.lower() in [t.lower() for t in terms]:
                category = cat
                break
        
        REACTION_DICTIONARY[pt] = {
            "pt": pt,
            "synonyms": [synonym],
            "patterns": [],
            "emoji": [],
            "category": category,
            "cluster_ids": []
        }
    else:
        # Add synonym to existing PT
        if synonym not in REACTION_DICTIONARY[pt]["synonyms"]:
            REACTION_DICTIONARY[pt]["synonyms"].append(synonym)

# Add emoji mappings
for emoji, reaction in EMOJI_AE_MAP.items():
    # Try to find PT for this reaction
    pt = map_to_meddra_pt(reaction)
    
    if pt not in REACTION_DICTIONARY:
        # Find category
        category = "Other"
        for cat, terms in REACTION_CATEGORIES.items():
            if reaction.lower() in [t.lower() for t in terms]:
                category = cat
                break
        
        REACTION_DICTIONARY[pt] = {
            "pt": pt,
            "synonyms": [reaction],
            "patterns": [],
            "emoji": [emoji],
            "category": category,
            "cluster_ids": []
        }
    else:
        # Add emoji to existing PT
        if emoji not in REACTION_DICTIONARY[pt]["emoji"]:
            REACTION_DICTIONARY[pt]["emoji"].append(emoji)
        # Add reaction as synonym if not already there
        if reaction not in REACTION_DICTIONARY[pt]["synonyms"]:
            REACTION_DICTIONARY[pt]["synonyms"].append(reaction)

# Add common patterns
PATTERN_ADDITIONS = {
    "Nausea": {
        "patterns": [r"\bnausea|nauseous|feeling sick|queasy|upset stomach\b"]
    },
    "Vomiting": {
        "patterns": [r"\bvomit|throwing up|threw up|puking|barf\b"]
    },
    "Headache": {
        "patterns": [r"\bheadache|migraine|head pain|pressure in head\b"]
    },
    "Dizziness": {
        "patterns": [r"\bdizzy|lightheaded|faint|vertigo|woozy\b"]
    },
    "Fatigue": {
        "patterns": [r"\bfatigue|tired|exhausted|drained|low energy\b"]
    },
    "Diarrhea": {
        "patterns": [r"\bdiarrhea|diarrhoea|loose stool|runs|upset bowels\b"]
    },
    "Palpitations": {
        "patterns": [r"\bheart racing|palpitations|fluttering|fast heartbeat|pounding heart\b"]
    },
    "Rash": {
        "patterns": [r"\brash|red spots|skin irritation|itchy skin\b"]
    }
}

for pt, additions in PATTERN_ADDITIONS.items():
    if pt in REACTION_DICTIONARY:
        REACTION_DICTIONARY[pt]["patterns"].extend(additions.get("patterns", []))


def get_reaction_pt(reaction: str) -> Optional[str]:
    """
    Get Preferred Term for a reaction.
    
    Args:
        reaction: Reaction term
    
    Returns:
        Preferred Term or None
    """
    reaction_lower = reaction.lower().strip()
    
    # Direct PT match
    if reaction in REACTION_DICTIONARY:
        return REACTION_DICTIONARY[reaction]["pt"]
    
    # Synonym match
    for pt, info in REACTION_DICTIONARY.items():
        if reaction_lower in [s.lower() for s in info["synonyms"]]:
            return pt
    
    # Use existing map_to_meddra_pt
    pt = map_to_meddra_pt(reaction)
    if pt and pt.lower() != reaction_lower:
        return pt
    
    return None


def get_reaction_category(pt: str) -> str:
    """
    Get category (SOC-like) for a Preferred Term.
    
    Args:
        pt: Preferred Term
    
    Returns:
        Category name
    """
    if pt in REACTION_DICTIONARY:
        return REACTION_DICTIONARY[pt]["category"]
    
    # Search in categories
    for category, terms in REACTION_CATEGORIES.items():
        if pt.lower() in [t.lower() for t in terms]:
            return category
    
    return "Other"


def get_all_pts() -> List[str]:
    """Get all Preferred Terms."""
    return list(REACTION_DICTIONARY.keys())


def get_synonyms(pt: str) -> List[str]:
    """Get synonyms for a Preferred Term."""
    if pt in REACTION_DICTIONARY:
        return REACTION_DICTIONARY[pt]["synonyms"]
    return []


def add_reaction_entry(pt: str, synonyms: List[str] = None, category: str = "Other", 
                       patterns: List[str] = None, emoji: List[str] = None):
    """
    Add or update a reaction entry in the dictionary.
    
    Args:
        pt: Preferred Term
        synonyms: List of synonyms
        category: Category name
        patterns: List of regex patterns
        emoji: List of emoji characters
    """
    if pt not in REACTION_DICTIONARY:
        REACTION_DICTIONARY[pt] = {
            "pt": pt,
            "synonyms": synonyms or [],
            "patterns": patterns or [],
            "emoji": emoji or [],
            "category": category,
            "cluster_ids": []
        }
    else:
        # Update existing
        if synonyms:
            REACTION_DICTIONARY[pt]["synonyms"].extend(synonyms)
            REACTION_DICTIONARY[pt]["synonyms"] = list(set(REACTION_DICTIONARY[pt]["synonyms"]))
        if patterns:
            REACTION_DICTIONARY[pt]["patterns"].extend(patterns)
        if emoji:
            REACTION_DICTIONARY[pt]["emoji"].extend(emoji)
            REACTION_DICTIONARY[pt]["emoji"] = list(set(REACTION_DICTIONARY[pt]["emoji"]))
        if category != "Other":
            REACTION_DICTIONARY[pt]["category"] = category

