"""
Social media slang to MedDRA mapping.
Maps informal language to standardized adverse event terms.
"""

import re
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd


# -----------------------------------------------
# Emoji → Adverse Event Mapping
# -----------------------------------------------
EMOJI_AE_MAP = {
    # Gastrointestinal
    "🤢": "nausea",
    "🤮": "vomiting",
    "😵": "dizziness",
    "🤕": "headache",
    "🤒": "pyrexia",
    "🤧": "cough",
    "😰": "anxiety",
    "😨": "panic attack",
    "😱": "acute distress",
    "😴": "fatigue",
    "💤": "lethargy",
    "💔": "tachycardia",
    "❤️‍🔥": "palpitations",
    "😵‍💫": "dizziness",
    "🫀": "cardiac disorder",
    "🫁": "dyspnoea",
    "😫": "fatigue",
    "😤": "dyspnoea",
    "🥵": "hot flush",
    "🥶": "chills",
    "🤮": "vomiting",  # Duplicate for emphasis
    "🤢": "nausea",  # Duplicate for emphasis
    "😷": "respiratory disorder",
    "🤕": "headache",  # Duplicate
    "😵": "dizziness",  # Duplicate
}


# -----------------------------------------------
# Slang to medical term mapping (Expanded to 200+ terms)
# -----------------------------------------------
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
    
    # Expanded Gastrointestinal (20+ terms)
    "throwing up": "vomiting",
    "puked": "vomiting",
    "barfed": "vomiting",
    "vomited": "vomiting",
    "nauseated": "nausea",
    "feeling sick": "nausea",
    "sick to stomach": "nausea",
    "stomach hurts": "abdominal pain",
    "belly ache": "abdominal pain",
    "gut pain": "abdominal pain",
    "cramps": "abdominal pain",
    "stomach cramps": "abdominal pain",
    "loose stools": "diarrhoea",
    "watery stool": "diarrhoea",
    "can't go": "constipation",
    "blocked up": "constipation",
    "bloated": "abdominal distension",
    "gas": "flatulence",
    "acid reflux": "gastrooesophageal reflux disease",
    "heartburn": "gastrooesophageal reflux disease",
    "indigestion": "dyspepsia",
    
    # Expanded Neurological (25+ terms)
    "dizzy spells": "dizziness",
    "vertigo": "dizziness",
    "spinning": "dizziness",
    "light headed": "dizziness",
    "head spinning": "dizziness",
    "head hurts": "headache",
    "head pounding": "headache",
    "migraine attack": "migraine",
    "brain foggy": "cognitive disorder",
    "can't focus": "cognitive disorder",
    "memory issues": "memory impairment",
    "forgetful": "memory impairment",
    "confusion": "confusional state",
    "disoriented": "confusional state",
    "foggy brain": "cognitive disorder",
    "mental fog": "cognitive disorder",
    "tremor": "tremor",
    "shaking": "tremor",
    "twitching": "muscle twitching",
    "numbness": "paraesthesia",
    "tingling": "paraesthesia",
    "pins and needles": "paraesthesia",
    "seizure": "seizure",
    "convulsion": "seizure",
    "blackout": "loss of consciousness",
    "fainted": "syncope",
    
    # Expanded Cardiovascular (15+ terms)
    "heart pounding": "palpitations",
    "heart fluttering": "palpitations",
    "irregular heartbeat": "arrhythmia",
    "skipped beat": "arrhythmia",
    "heart thumping": "palpitations",
    "pulse racing": "tachycardia",
    "high heart rate": "tachycardia",
    "chest hurts": "chest pain",
    "chest pressure": "chest discomfort",
    "tight chest": "chest discomfort",
    "heartburn": "chest discomfort",
    "shortness of breath": "dyspnoea",
    "can't catch breath": "dyspnoea",
    "breathless": "dyspnoea",
    "winded": "dyspnoea",
    
    # Expanded Dermatological (15+ terms)
    "skin rash": "rash",
    "breaking out": "rash",
    "hives": "urticaria",
    "welts": "urticaria",
    "itchy skin": "pruritus",
    "itching": "pruritus",
    "redness": "erythema",
    "red patches": "erythema",
    "swelling": "oedema",
    "puffy": "oedema",
    "dry skin": "xerosis",
    "peeling": "skin exfoliation",
    "blisters": "blister",
    "sores": "ulcer",
    "bruising": "contusion",
    
    # Expanded Musculoskeletal (15+ terms)
    "joints hurt": "arthralgia",
    "achy joints": "arthralgia",
    "muscle aches": "myalgia",
    "sore all over": "myalgia",
    "back hurts": "back pain",
    "lower back pain": "back pain",
    "neck pain": "neck pain",
    "shoulder pain": "shoulder pain",
    "knee pain": "knee pain",
    "stiff": "musculoskeletal stiffness",
    "stiffness": "musculoskeletal stiffness",
    "cramping": "muscle spasms",
    "muscle cramps": "muscle spasms",
    "weakness": "asthenia",
    "feeling weak": "asthenia",
    
    # Expanded Respiratory (15+ terms)
    "out of breath": "dyspnoea",
    "breathing hard": "dyspnoea",
    "wheezing": "wheezing",
    "coughing": "cough",
    "dry cough": "cough",
    "persistent cough": "cough",
    "congestion": "nasal congestion",
    "stuffy nose": "nasal congestion",
    "runny nose": "rhinorrhoea",
    "sneezing": "sneezing",
    "sore throat": "pharyngolaryngeal pain",
    "throat hurts": "pharyngolaryngeal pain",
    "hoarse": "dysphonia",
    "voice changes": "dysphonia",
    "chest congestion": "respiratory disorder",
    
    # Expanded Psychiatric (20+ terms)
    "anxiety attack": "panic attack",
    "panic attacks": "panic attack",
    "feeling anxious": "anxiety",
    "worried": "anxiety",
    "nervous": "anxiety",
    "on edge": "anxiety",
    "irritable": "irritability",
    "moody": "mood altered",
    "emotional": "mood altered",
    "sad": "depression",
    "down": "depression",
    "feeling down": "depression",
    "hopeless": "depression",
    "suicidal thoughts": "suicidal ideation",
    "mania": "mania",
    "manic": "mania",
    "agitated": "agitation",
    "restless": "restlessness",
    "can't sit still": "restlessness",
    "racing thoughts": "racing thoughts",
    
    # Expanded Endocrine (10+ terms)
    "hot flashes": "hot flush",
    "night sweats": "sweating",
    "sweating a lot": "hyperhidrosis",
    "cold sweats": "sweating",
    "feeling cold": "chills",
    "shivering": "chills",
    "thirsty": "polydipsia",
    "always thirsty": "polydipsia",
    "frequent urination": "pollakiuria",
    "peeing a lot": "pollakiuria",
    
    # Injection-site reactions (10+ terms)
    "injection site pain": "injection site pain",
    "shot hurts": "injection site pain",
    "red at injection": "injection site erythema",
    "swollen at injection": "injection site swelling",
    "lump at injection": "injection site mass",
    "bruise at injection": "injection site bruising",
    "itchy at injection": "injection site pruritus",
    "warm at injection": "injection site warmth",
    "hard at injection": "injection site induration",
    "tender at injection": "injection site pain",
    
    # GLP-1 / Weight loss specific (10+ terms)
    "sulfur burps": "eructation",
    "sulphur burps": "eructation",
    "rotten egg burps": "eructation",
    "sulfur taste": "dysgeusia",
    "metallic taste": "dysgeusia",
    "taste changes": "dysgeusia",
    "food aversion": "decreased appetite",
    "not hungry": "decreased appetite",
    "loss of appetite": "decreased appetite",
    "early satiety": "early satiety",
    
    # Ocular (10+ terms)
    "blurry vision": "vision blurred",
    "blurred vision": "vision blurred",
    "double vision": "diplopia",
    "eye pain": "eye pain",
    "dry eyes": "dry eye",
    "watery eyes": "lacrimation increased",
    "sensitive to light": "photophobia",
    "eye irritation": "eye irritation",
    "red eyes": "conjunctival hyperaemia",
    "vision problems": "vision blurred",
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


def extract_emoji_reactions(text: str) -> List[str]:
    """
    Extract adverse events implied by emojis in the post.
    
    Args:
        text: Social media post text
    
    Returns:
        List of standardized reaction terms found via emojis
    """
    if not isinstance(text, str):
        return []
    
    mapped = []
    for char in text:
        if char in EMOJI_AE_MAP:
            mapped.append(EMOJI_AE_MAP[char])
    
    # Deduplicate while preserving order
    seen = set()
    unique_mapped = []
    for reaction in mapped:
        if reaction not in seen:
            seen.add(reaction)
            unique_mapped.append(reaction)
    
    return unique_mapped


def extract_multiple_reactions(text: str, return_confidence: bool = False) -> Union[List[Tuple[str, float]], List[str]]:
    """
    Extract multiple adverse events from a single post.
    
    This function identifies all reactions mentioned in the text, not just the first one.
    It handles:
    - Multiple reactions separated by commas, "and", "&", "/", ";", newlines
    - Emoji-based reactions
    - Slang-based reactions
    - Pattern-based reactions
    - Negation detection (excludes negated reactions)
    
    Args:
        text: Social media post text
        return_confidence: If True, returns list of (reaction, confidence) tuples
    
    Returns:
        List of standardized reaction terms, or list of (reaction, confidence) tuples
    """
    if not text or not isinstance(text, str):
        return [] if not return_confidence else []
    
    text_lower = text.lower()
    all_reactions = {}  # Dict to store unique reactions with their max confidence
    
    # 1. Extract emoji-based reactions
    emoji_reactions = extract_emoji_reactions(text)
    for reaction in emoji_reactions:
        if reaction not in all_reactions:
            all_reactions[reaction] = 0.85  # Emoji = high confidence
    
    # 2. Extract slang-based reactions (check all matches, not just first)
    for slang, mapped_reaction in SLANG_MAP.items():
        if slang in text_lower:
            # Check if this is negated
            if _is_negated(text_lower, slang):
                continue  # Skip negated reactions
            if mapped_reaction not in all_reactions:
                all_reactions[mapped_reaction] = 0.9  # Exact slang match = high confidence
            elif all_reactions[mapped_reaction] < 0.9:
                all_reactions[mapped_reaction] = 0.9
    
    # 3. Extract pattern-based reactions
    for pattern, mapped_reaction in PATTERN_MAP:
        if re.search(pattern, text_lower, re.IGNORECASE):
            if _is_negated(text_lower, pattern):
                continue
            if mapped_reaction not in all_reactions:
                all_reactions[mapped_reaction] = 0.7  # Pattern match = medium confidence
            elif all_reactions[mapped_reaction] < 0.7:
                all_reactions[mapped_reaction] = 0.7
    
    # 4. Boost confidence if drug context present
    drug_indicators = [
        r'\b(took|taking|on|using|started|stopped)\s+\w+',
        r'\b(drug|medication|medicine|prescription)\b',
    ]
    has_drug_context = any(re.search(indicator, text_lower) for indicator in drug_indicators)
    if has_drug_context:
        for reaction in all_reactions:
            all_reactions[reaction] = min(1.0, all_reactions[reaction] + 0.1)
    
    # 5. Reduce confidence if overall negation detected
    overall_negation = re.search(r'\b(no|not|never|didn\'t|doesn\'t|won\'t|isn\'t)\s+(side\s+effects?|adverse|reactions?)', text_lower)
    if overall_negation:
        for reaction in all_reactions:
            all_reactions[reaction] = max(0.2, all_reactions[reaction] - 0.3)
    
    # Convert to list format
    if return_confidence:
        return [(reaction, conf) for reaction, conf in sorted(all_reactions.items(), key=lambda x: x[1], reverse=True)]
    else:
        return list(all_reactions.keys())


def _is_negated(text: str, term: str) -> bool:
    """
    Check if a term is negated in the text.
    
    Args:
        text: Lowercase text
        term: Term to check for negation
    
    Returns:
        True if term appears to be negated
    """
    # Find position of term
    term_pos = text.find(term)
    if term_pos == -1:
        return False
    
    # Check for negation words before the term (within 10 words)
    before_text = text[max(0, term_pos - 100):term_pos]
    negation_patterns = [
        r'\b(no|not|never|didn\'t|doesn\'t|won\'t|isn\'t|wasn\'t|weren\'t)\s+\w*\s*$',
        r'\b(without|lack of|absence of)\s+',
    ]
    
    for pattern in negation_patterns:
        if re.search(pattern, before_text, re.IGNORECASE):
            return True
    
    return False


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
    
    # First check emoji-based reactions (high confidence for emoji detection)
    emoji_reactions = extract_emoji_reactions(text)
    if emoji_reactions:
        reaction = emoji_reactions[0]  # Take first emoji reaction
        confidence = 0.85  # Emoji detection = high confidence
    
    # Then check exact slang matches (highest confidence)
    if not reaction:
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
    
    # If emoji reactions found but no text reaction, use emoji reaction
    if not reaction and emoji_reactions:
        reaction = emoji_reactions[0]
        confidence = 0.85
    
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


def extract_reactions_from_posts(df: pd.DataFrame, include_confidence: bool = True, multi_ae: bool = True) -> pd.DataFrame:
    """
    Extract and map reactions from social media posts.
    
    Args:
        df: DataFrame with cleaned posts (from social_cleaner)
        include_confidence: If True, adds confidence_score column
        multi_ae: If True, extracts multiple reactions per post (default: True)
    
    Returns:
        DataFrame with added 'reaction' (or 'reactions' if multi_ae=True) and optionally 'confidence_score' columns
    """
    if df.empty or "text" not in df.columns:
        return df
    
    if multi_ae:
        # Multi-AE extraction mode
        reactions_list = []
        confidence_scores = []
        max_confidence_scores = []
        
        for text in df["text"]:
            result = extract_multiple_reactions(str(text), return_confidence=include_confidence)
            
            if include_confidence and result:
                # result is list of (reaction, confidence) tuples
                reactions_with_conf = result
                reactions = [r[0] for r in reactions_with_conf]
                confidences = [r[1] for r in reactions_with_conf]
                reactions_list.append(reactions)
                confidence_scores.append(confidences)
                max_confidence_scores.append(max(confidences) if confidences else 0.0)
            elif result:
                # result is list of reaction strings
                reactions_list.append(result)
                confidence_scores.append([])
                max_confidence_scores.append(0.0)
            else:
                reactions_list.append([])
                confidence_scores.append([])
                max_confidence_scores.append(0.0)
        
        # Store as JSON-serializable format (list of strings)
        df["reactions"] = reactions_list
        df["reaction"] = df["reactions"].apply(lambda x: ", ".join(x) if x else None)  # For backward compatibility
        df["reaction_count"] = df["reactions"].apply(len)
        
        if include_confidence:
            df["confidence_scores"] = confidence_scores  # List of confidence scores per reaction
            df["confidence_score"] = max_confidence_scores  # Max confidence for filtering
            df["confidence_level"] = df["confidence_score"].apply(
                lambda x: "High" if x >= 0.8 else "Medium" if x >= 0.5 else "Low" if x > 0 else "None"
            )
    else:
        # Single-AE extraction mode (backward compatibility)
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
            df["confidence_level"] = df["confidence_score"].apply(
                lambda x: "High" if x >= 0.8 else "Medium" if x >= 0.5 else "Low" if x > 0 else "None"
            )
    
    # Flag for posts with detected reactions
    if multi_ae:
        df["has_reaction"] = df["reaction_count"] > 0
    else:
        df["has_reaction"] = df["reaction"].notna()
    
    return df


def get_reaction_summary(df: pd.DataFrame, multi_ae: bool = True) -> Dict[str, int]:
    """
    Get summary of detected reactions.
    
    Args:
        df: DataFrame with reactions mapped
        multi_ae: If True, uses 'reactions' column (list), else uses 'reaction' column
    
    Returns:
        Dictionary mapping reaction terms to counts
    """
    if df.empty:
        return {}
    
    reaction_counts = {}
    
    if multi_ae and "reactions" in df.columns:
        # Count from multi-AE reactions list
        for reactions_list in df["reactions"]:
            if isinstance(reactions_list, list):
                for reaction in reactions_list:
                    if reaction:
                        reaction_counts[reaction] = reaction_counts.get(reaction, 0) + 1
    elif "reaction" in df.columns:
        # Count from single reaction column
        reaction_counts = df["reaction"].value_counts().to_dict()
        # Remove None/NaN
        reaction_counts = {k: v for k, v in reaction_counts.items() if pd.notna(k) and k}
    
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

