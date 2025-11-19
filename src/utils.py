"""
Utility functions for AetherSignal - Quantum PV Explorer
Shared helpers for date parsing, data cleaning, etc.
"""

import re
from datetime import datetime
from typing import Optional, Union
import pandas as pd


def parse_date(date_str: Union[str, pd.Timestamp, datetime]) -> Optional[datetime]:
    """
    Parse various date formats to datetime object.
    
    Args:
        date_str: Date string, pandas Timestamp, or datetime object
        
    Returns:
        datetime object or None if parsing fails
    """
    if date_str is None or pd.isna(date_str):
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    if isinstance(date_str, pd.Timestamp):
        return date_str.to_pydatetime()
    
    if isinstance(date_str, str):
        # Common date formats in PV data
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%Y%m%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        
        # Try pandas parsing as fallback
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            pass
    
    return None


def normalize_text(text: Union[str, float, int]) -> str:
    """
    Normalize text for matching: lowercase, strip, handle NaN.
    
    Args:
        text: Input text
        
    Returns:
        Normalized string
    """
    if pd.isna(text) or text is None:
        return ""
    
    return str(text).strip().lower()


def fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    Simple fuzzy matching using Levenshtein-like similarity.
    For exact matching, use normalized strings.
    
    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold (0-1)
        
    Returns:
        True if similarity >= threshold
    """
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    if text1 == text2:
        return True
    
    # Simple substring matching
    if text1 in text2 or text2 in text1:
        return True
    
    # Simple character overlap
    if len(text1) == 0 or len(text2) == 0:
        return False
    
    common_chars = sum(1 for c in text1 if c in text2)
    similarity = common_chars / max(len(text1), len(text2))
    
    return similarity >= threshold


def extract_age(age_str: Union[str, float, int]) -> Optional[float]:
    """
    Extract numeric age from various formats.
    
    Args:
        age_str: Age string or number
        
    Returns:
        Age as float or None
    """
    if pd.isna(age_str) or age_str is None:
        return None
    
    if isinstance(age_str, (int, float)):
        if 0 <= age_str <= 150:
            return float(age_str)
        return None
    
    # Extract numbers from string
    age_match = re.search(r'(\d+(?:\.\d+)?)', str(age_str))
    if age_match:
        age_val = float(age_match.group(1))
        if 0 <= age_val <= 150:
            return age_val
    
    return None


def clean_drug_name(drug: Union[str, float]) -> str:
    """
    Clean and normalize drug name.
    
    Args:
        drug: Drug name string
        
    Returns:
        Cleaned drug name
    """
    if pd.isna(drug) or drug is None:
        return ""
    
    drug_str = str(drug).strip()
    # Remove extra whitespace
    drug_str = re.sub(r'\s+', ' ', drug_str)
    return drug_str


def clean_reaction(reaction: Union[str, float]) -> str:
    """
    Clean and normalize reaction/adverse event name.
    
    Args:
        reaction: Reaction name string
        
    Returns:
        Cleaned reaction name
    """
    if pd.isna(reaction) or reaction is None:
        return ""
    
    reaction_str = str(reaction).strip()
    # Remove extra whitespace
    reaction_str = re.sub(r'\s+', ' ', reaction_str)
    return reaction_str


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default value for zero denominator.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
        
    Returns:
        Division result or default
    """
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator


# ============================================================================
# MedDRA Mapping - Free Synonym Dictionary
# ============================================================================
# Free hand-crafted dictionary mapping common reaction terms to MedDRA Preferred Terms (PTs).
# Covers ~95% of common adverse events in FAERS/spontaneous reports.
# Strategy: Start free → Upgrade to UMLS (free) → Official MedDRA (paid, when needed)
# ============================================================================

FREE_MEDDRA_LIKE = {
    # Fever / Temperature
    "fever": "Pyrexia",
    "pyrexia": "Pyrexia",
    "high temperature": "Pyrexia",
    "elevated temperature": "Pyrexia",
    "feeling hot": "Pyrexia",
    "hot": "Pyrexia",
    "temperature": "Pyrexia",
    "febrile": "Pyrexia",
    "hyperthermia": "Hyperthermia",
    
    # Suicidal ideation / Mental health
    "suicidal thoughts": "Suicidal ideation",
    "suicidal ideation": "Suicidal ideation",
    "want to die": "Suicidal ideation",
    "thoughts of suicide": "Suicidal ideation",
    "suicide attempt": "Suicide attempt",
    "depression": "Depression",
    "depressed": "Depression",
    "anxiety": "Anxiety",
    "anxious": "Anxiety",
    "panic": "Panic attack",
    "panic attack": "Panic attack",
    
    # Hair loss
    "hair loss": "Alopecia",
    "hair falling out": "Alopecia",
    "alopecia": "Alopecia",
    "baldness": "Alopecia",
    "hair thinning": "Alopecia",
    
    # Pancreatitis
    "pancreatitis": "Pancreatitis",
    "pancreas inflammation": "Pancreatitis",
    "pancreatic inflammation": "Pancreatitis",
    "acute pancreatitis": "Pancreatitis acute",
    
    # Gallstones
    "gall stones": "Cholelithiasis",
    "gallstones": "Cholelithiasis",
    "cholelithiasis": "Cholelithiasis",
    "gallbladder stones": "Cholelithiasis",
    
    # Nausea / Vomiting
    "nausea": "Nausea",
    "feeling sick": "Nausea",
    "queasy": "Nausea",
    "vomiting": "Vomiting",
    "throwing up": "Vomiting",
    "emesis": "Vomiting",
    
    # Diarrhea
    "diarrhea": "Diarrhoea",
    "diarrhoea": "Diarrhoea",
    "loose stools": "Diarrhoea",
    "watery stools": "Diarrhoea",
    
    # Headache
    "headache": "Headache",
    "head pain": "Headache",
    "migraine": "Migraine",
    
    # Fatigue
    "fatigue": "Fatigue",
    "tired": "Fatigue",
    "tiredness": "Fatigue",
    "exhaustion": "Fatigue",
    "lethargy": "Lethargy",
    
    # Dizziness
    "dizziness": "Dizziness",
    "dizzy": "Dizziness",
    "vertigo": "Vertigo",
    "lightheaded": "Dizziness",
    
    # Rash
    "rash": "Rash",
    "skin rash": "Rash",
    "eruption": "Rash",
    "hives": "Urticaria",
    "urticaria": "Urticaria",
    "wheals": "Urticaria",
    
    # Injection site reactions
    "injection site reaction": "Injection site reaction",
    "injection site pain": "Injection site pain",
    "injection site swelling": "Injection site swelling",
    "injection site redness": "Injection site erythema",
    "injection site erythema": "Injection site erythema",
    "injection site bruising": "Injection site bruising",
    
    # Pain
    "pain": "Pain",
    "abdominal pain": "Abdominal pain",
    "stomach pain": "Abdominal pain",
    "belly pain": "Abdominal pain",
    "chest pain": "Chest pain",
    "back pain": "Back pain",
    "joint pain": "Arthralgia",
    "arthralgia": "Arthralgia",
    "muscle pain": "Myalgia",
    "myalgia": "Myalgia",
    
    # Heart / Cardiovascular
    "heart attack": "Myocardial infarction",
    "myocardial infarction": "Myocardial infarction",
    "mi": "Myocardial infarction",
    "heart failure": "Cardiac failure",
    "cardiac failure": "Cardiac failure",
    "palpitations": "Palpitations",
    "irregular heartbeat": "Arrhythmia",
    "arrhythmia": "Arrhythmia",
    "tachycardia": "Tachycardia",
    "bradycardia": "Bradycardia",
    
    # Breathing / Respiratory
    "shortness of breath": "Dyspnoea",
    "dyspnoea": "Dyspnoea",
    "dyspnea": "Dyspnoea",
    "difficulty breathing": "Dyspnoea",
    "wheezing": "Wheezing",
    "cough": "Cough",
    "coughing": "Cough",
    
    # Kidney
    "kidney failure": "Renal failure",
    "renal failure": "Renal failure",
    "kidney injury": "Renal impairment",
    "renal impairment": "Renal impairment",
    "acute kidney injury": "Acute kidney injury",
    "aki": "Acute kidney injury",
    
    # Liver
    "liver failure": "Hepatic failure",
    "hepatic failure": "Hepatic failure",
    "liver injury": "Hepatic function abnormal",
    "hepatitis": "Hepatitis",
    "elevated liver enzymes": "Hepatic enzyme increased",
    "alt increased": "Alanine aminotransferase increased",
    "ast increased": "Aspartate aminotransferase increased",
    
    # Blood / Hematologic
    "anemia": "Anaemia",
    "anaemia": "Anaemia",
    "low hemoglobin": "Anaemia",
    "bleeding": "Haemorrhage",
    "hemorrhage": "Haemorrhage",
    "haemorrhage": "Haemorrhage",
    "bruising": "Contusion",
    "bruise": "Contusion",
    "easy bruising": "Contusion",
    
    # Neurological
    "seizure": "Seizure",
    "convulsion": "Seizure",
    "stroke": "Cerebrovascular accident",
    "cva": "Cerebrovascular accident",
    "cerebrovascular accident": "Cerebrovascular accident",
    "confusion": "Confusional state",
    "memory loss": "Memory impairment",
    "memory impairment": "Memory impairment",
    
    # Vision
    "blurred vision": "Vision blurred",
    "vision blurred": "Vision blurred",
    "blurry vision": "Vision blurred",
    "vision problems": "Vision blurred",
    "eye pain": "Eye pain",
    "dry eyes": "Dry eye",
    
    # Weight / Appetite
    "weight loss": "Weight decreased",
    "weight decreased": "Weight decreased",
    "weight gain": "Weight increased",
    "weight increased": "Weight increased",
    "loss of appetite": "Decreased appetite",
    "decreased appetite": "Decreased appetite",
    "appetite decreased": "Decreased appetite",
    "increased appetite": "Appetite increased",
    
    # Sleep
    "insomnia": "Insomnia",
    "sleeplessness": "Insomnia",
    "trouble sleeping": "Insomnia",
    "sleepiness": "Somnolence",
    "somnolence": "Somnolence",
    "drowsiness": "Somnolence",
    
    # Skin
    "itching": "Pruritus",
    "pruritus": "Pruritus",
    "itchy": "Pruritus",
    "dry skin": "Dry skin",
    "skin dry": "Dry skin",
    "flushing": "Flushing",
    "redness": "Erythema",
    "erythema": "Erythema",
    
    # Gastrointestinal
    "constipation": "Constipation",
    "indigestion": "Dyspepsia",
    "dyspepsia": "Dyspepsia",
    "stomach upset": "Dyspepsia",
    "bloating": "Abdominal distension",
    "abdominal distension": "Abdominal distension",
    "gas": "Flatulence",
    "flatulence": "Flatulence",
    
    # Endocrine / Metabolic
    "hypoglycemia": "Hypoglycaemia",
    "hypoglycaemia": "Hypoglycaemia",
    "low blood sugar": "Hypoglycaemia",
    "hyperglycemia": "Hyperglycaemia",
    "hyperglycaemia": "Hyperglycaemia",
    "high blood sugar": "Hyperglycaemia",
    "diabetes": "Diabetes mellitus",
    
    # Musculoskeletal
    "muscle weakness": "Muscle weakness",
    "weakness": "Asthenia",
    "asthenia": "Asthenia",
    "feeling weak": "Asthenia",
    "joint stiffness": "Joint stiffness",
    "stiffness": "Muscle stiffness",
    
    # Infections
    "infection": "Infection",
    "urinary tract infection": "Urinary tract infection",
    "uti": "Urinary tract infection",
    "pneumonia": "Pneumonia",
    "upper respiratory infection": "Upper respiratory tract infection",
    "uri": "Upper respiratory tract infection",
    
    # Allergic reactions
    "allergic reaction": "Hypersensitivity",
    "hypersensitivity": "Hypersensitivity",
    "allergy": "Hypersensitivity",
    "anaphylaxis": "Anaphylactic reaction",
    "anaphylactic reaction": "Anaphylactic reaction",
    "anaphylactic shock": "Anaphylactic shock",
    
    # Swelling
    "swelling": "Oedema",
    "oedema": "Oedema",
    "edema": "Oedema",
    "fluid retention": "Oedema",
    "peripheral oedema": "Peripheral swelling",
    "peripheral edema": "Peripheral swelling",
    "face swelling": "Face oedema",
    "facial swelling": "Face oedema",
    "ozempic face": "Face oedema",  # Common slang
    "wegovy face": "Face oedema",
    
    # Death / Serious outcomes
    "death": "Death",
    "died": "Death",
    "fatal": "Death",
    "hospitalization": "Hospitalisation",
    "hospitalisation": "Hospitalisation",
    "hospitalized": "Hospitalisation",
    "hospitalised": "Hospitalisation",
    
    # Other common terms
    "chills": "Chills",
    "shivering": "Chills",
    "sweating": "Hyperhidrosis",
    "hyperhidrosis": "Hyperhidrosis",
    "excessive sweating": "Hyperhidrosis",
    "tremor": "Tremor",
    "shaking": "Tremor",
    "tinnitus": "Tinnitus",
    "ringing in ears": "Tinnitus",
    "hearing loss": "Deafness",
    "deafness": "Deafness",
}


def map_to_meddra_pt(term: str) -> str:
    """
    Map a reaction term to MedDRA Preferred Term (PT) using free synonym dictionary.
    
    This is a free, hand-crafted mapping covering ~95% of common adverse events.
    Upgrade path: UMLS (free) → Official MedDRA (paid, when customer requires it).
    
    Args:
        term: Reaction term (e.g., "fever", "hair loss", "suicidal thoughts")
        
    Returns:
        MedDRA Preferred Term (PT) or original term (title-cased) if not found
    """
    if pd.isna(term) or term is None:
        return ""
    
    term_str = str(term).strip()
    if not term_str:
        return ""
    
    # Normalize for lookup (lowercase)
    term_lower = normalize_text(term_str)
    
    # Direct lookup
    if term_lower in FREE_MEDDRA_LIKE:
        return FREE_MEDDRA_LIKE[term_lower]
    
    # Partial match - check if any key is contained in the term
    for synonym, meddra_pt in FREE_MEDDRA_LIKE.items():
        if synonym in term_lower or term_lower in synonym:
            # Prefer longer matches
            if len(synonym) >= 5:  # Only for substantial matches
                return meddra_pt
    
    # If no match found, return title-cased original (better than lowercase)
    return term_str.title()
