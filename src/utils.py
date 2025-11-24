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
    
    For drug names, use drug_name_normalization.fuzzy_match_drugs() instead.
    
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
    
    # Off-label use / Product use issues
    "off label use": "Off label use",
    "off-label use": "Off label use",
    "off label": "Off label use",
    "off-label": "Off label use",
    "product use in unapproved indication": "Off label use",
    "unapproved use": "Off label use",
    "incorrect dose administered": "Incorrect dose administered",
    "drug ineffective": "Drug ineffective",
    "product ineffective": "Drug ineffective",
    "treatment failure": "Drug ineffective",
    
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
    
    # Injection Site Reactions (expanded - most common in FAERS 2025)
    "injection site reaction": "Injection site reaction",
    "injection site pain": "Injection site pain",
    "injection site swelling": "Injection site swelling",
    "injection site redness": "Injection site erythema",
    "injection site erythema": "Injection site erythema",
    "injection site bruising": "Injection site bruising",
    "injection site induration": "Injection site induration",
    "injection site pruritus": "Injection site pruritus",
    "injection site warmth": "Injection site warmth",
    "injection site nodule": "Injection site nodule",
    "shot site pain": "Injection site pain",
    "shot hurts": "Injection site pain",
    "arm sore after shot": "Injection site pain",
    "red lump at injection site": "Injection site swelling",
    "sore arm": "Injection site pain",
    "injection site bleeding": "Injection site haemorrhage",
    "injection site haemorrhage": "Injection site haemorrhage",
    "injection site hematoma": "Injection site haematoma",
    "injection site haematoma": "Injection site haematoma",
    "injection site abscess": "Injection site abscess",
    "injection site cellulitis": "Injection site cellulitis",
    
    # Cardiac / Cardiovascular (patient language)
    "heart racing": "Palpitations",
    "heart pounding": "Palpitations",
    "heart fluttering": "Palpitations",
    "irregular heartbeat": "Arrhythmia",
    "skipped beats": "Arrhythmia",
    "chest tight": "Chest discomfort",
    "chest tightness": "Chest discomfort",
    "chest discomfort": "Chest discomfort",
    "heart attack symptoms": "Myocardial infarction",
    "heart stopped": "Cardiac arrest",
    "cardiac arrest": "Cardiac arrest",
    "heart stopped beating": "Cardiac arrest",
    "low blood pressure": "Hypotension",
    "hypotension": "Hypotension",
    "high blood pressure": "Hypertension",
    "hypertension": "Hypertension",
    "bp high": "Hypertension",
    "bp low": "Hypotension",
    
    # Neurological / Cognitive (patient language)
    "brain fog": "Cognitive disorder",
    "can't think straight": "Cognitive disorder",
    "cognitive disorder": "Cognitive disorder",
    "memory problems": "Memory impairment",
    "memory issues": "Memory impairment",
    "forgetful": "Memory impairment",
    "can't remember": "Memory impairment",
    "confused": "Confusional state",
    "disoriented": "Confusional state",
    "feeling lost": "Confusional state",
    "dizzy spells": "Dizziness",
    "lightheadedness": "Dizziness",
    "feeling faint": "Syncope",
    "fainting": "Syncope",
    "syncope": "Syncope",
    "passed out": "Syncope",
    "blacked out": "Syncope",
    
    # Mental Health / Psychiatric (patient language)
    "crying all the time": "Depressed mood",
    "feeling blue": "Depression",
    "feeling down": "Depression",
    "sad all the time": "Depression",
    "mood swings": "Mood swings",
    "mood changes": "Mood altered",
    "irritable": "Irritability",
    "moody": "Mood altered",
    "aggressive": "Aggression",
    "agitation": "Agitation",
    "restless": "Restlessness",
    "can't sit still": "Restlessness",
    "mania": "Mania",
    "manic": "Mania",
    "psychosis": "Psychotic disorder",
    "hallucinations": "Hallucination",
    "hearing voices": "Hallucination",
    "seeing things": "Hallucination",
    "paranoia": "Paranoia",
    "paranoid": "Paranoia",
    
    # British vs American Spelling (critical for international data)
    "diarrhoea": "Diarrhoea",  # British
    "diarrhea": "Diarrhoea",   # American (already have, but ensuring both)
    "anaemia": "Anaemia",       # British
    "anemia": "Anaemia",        # American (already have)
    "oedema": "Oedema",         # British
    "edema": "Oedema",          # American (already have)
    "haemorrhage": "Haemorrhage", # British
    "hemorrhage": "Haemorrhage",  # American (already have)
    "haematoma": "Haematoma",   # British
    "hematoma": "Haematoma",    # American
    "leukaemia": "Leukaemia",   # British
    "leukemia": "Leukaemia",    # American
    "tumour": "Tumour",         # British
    "tumor": "Tumour",          # American
    "oesophagus": "Oesophageal disorder", # British
    "esophagus": "Oesophageal disorder",  # American
    
    # Medical Abbreviations (common in reports)
    "mi": "Myocardial infarction",
    "dvt": "Deep vein thrombosis",
    "pe": "Pulmonary embolism",
    "tia": "Transient ischaemic attack",
    "uti": "Urinary tract infection",
    "copd": "Chronic obstructive pulmonary disease",
    "chf": "Cardiac failure",
    "aki": "Acute kidney injury",
    "arf": "Acute renal failure",
    "ards": "Acute respiratory distress syndrome",
    "gi": "Gastrointestinal disorder",
    "gerd": "Gastrooesophageal reflux disease",
    "ibd": "Inflammatory bowel disease",
    "ibs": "Irritable bowel syndrome",
    "pvd": "Peripheral vascular disorder",
    "cva": "Cerebrovascular accident",
    "afib": "Atrial fibrillation",
    "svt": "Supraventricular tachycardia",
    "vt": "Ventricular tachycardia",
    "vfib": "Ventricular fibrillation",
    
    # Pregnancy & Reproductive Health
    "miscarriage": "Spontaneous abortion",
    "spontaneous abortion": "Spontaneous abortion",
    "bleeding while pregnant": "Vaginal haemorrhage",
    "vaginal bleeding": "Vaginal haemorrhage",
    "spotting": "Vaginal haemorrhage",
    "bleeding during pregnancy": "Vaginal haemorrhage",
    "pregnancy complications": "Pregnancy complication",
    "ectopic pregnancy": "Ectopic pregnancy",
    "stillbirth": "Stillbirth",
    "premature birth": "Premature baby",
    "preterm birth": "Premature baby",
    "birth defects": "Congenital anomaly",
    "congenital anomaly": "Congenital anomaly",
    "birth defect": "Congenital anomaly",
    
    # Pediatric-Specific Terms
    "baby rash": "Rash",
    "infant rash": "Rash",
    "child rash": "Rash",
    "fever in baby": "Pyrexia",
    "baby fever": "Pyrexia",
    "infant fever": "Pyrexia",
    "child fever": "Pyrexia",
    "baby won't eat": "Feeding disorder",
    "feeding problems": "Feeding disorder",
    "feeding disorder": "Feeding disorder",
    "failure to thrive": "Failure to thrive",
    "baby not growing": "Failure to thrive",
    "developmental delay": "Developmental delay",
    "delayed milestones": "Developmental delay",
    "colic": "Infantile colic",
    "baby colic": "Infantile colic",
    
    # Elderly-Specific Terms
    "falls": "Fall",
    "falling": "Fall",
    "fell down": "Fall",
    "frequent falls": "Fall",
    "balance problems": "Balance disorder",
    "unsteady": "Balance disorder",
    "dizzy when standing": "Orthostatic hypotension",
    "orthostatic hypotension": "Orthostatic hypotension",
    "low bp when standing": "Orthostatic hypotension",
    "incontinence": "Urinary incontinence",
    "urinary incontinence": "Urinary incontinence",
    "accidental urination": "Urinary incontinence",
    "memory loss in elderly": "Memory impairment",
    "confusion in elderly": "Confusional state",
    
    # Additional Common Patient Terms
    "feeling sick": "Nausea",  # Already have, but ensuring coverage
    "threw up": "Vomiting",
    "puking": "Vomiting",
    "throwing up": "Vomiting",
    "barfing": "Vomiting",
    "feeling nauseous": "Nausea",
    "queasy stomach": "Nausea",
    "upset stomach": "Dyspepsia",
    "stomach upset": "Dyspepsia",
    "indigestion": "Dyspepsia",
    "heartburn": "Gastrooesophageal reflux disease",
    "acid reflux": "Gastrooesophageal reflux disease",
    "reflux": "Gastrooesophageal reflux disease",
    "can't sleep": "Insomnia",
    "trouble sleeping": "Insomnia",
    "sleepless": "Insomnia",
    "waking up at night": "Insomnia",
    "sleep problems": "Sleep disorder",
    "sleep disorder": "Sleep disorder",
    "too sleepy": "Somnolence",
    "sleepy all day": "Somnolence",
    "excessive sleepiness": "Somnolence",
    "can't stay awake": "Somnolence",
    
    # Additional Skin Terms
    "dry skin": "Dry skin",
    "skin dry": "Dry skin",
    "flaky skin": "Dry skin",
    "peeling skin": "Skin exfoliation",
    "skin peeling": "Skin exfoliation",
    "blisters": "Blister",
    "blistering": "Blister",
    "sores": "Ulcer",
    "open sores": "Ulcer",
    "skin ulcers": "Ulcer",
    "wounds not healing": "Wound",
    "slow healing": "Wound",
    "acne": "Acne",
    "pimples": "Acne",
    "breakout": "Acne",
    "skin breakout": "Acne",
    
    # Additional Pain Terms
    "hurts": "Pain",
    "aching": "Pain",
    "sore": "Pain",
    "tender": "Pain",
    "stabbing pain": "Pain",
    "sharp pain": "Pain",
    "burning pain": "Pain",
    "throbbing pain": "Pain",
    "stomach hurts": "Abdominal pain",
    "belly hurts": "Abdominal pain",
    "tummy hurts": "Abdominal pain",
    "chest hurts": "Chest pain",
    "back hurts": "Back pain",
    "head hurts": "Headache",
    "sore throat": "Pharyngitis",
    "throat pain": "Pharyngitis",
    "throat sore": "Pharyngitis",
    "ear pain": "Ear pain",
    "earache": "Ear pain",
    "tooth pain": "Toothache",
    "toothache": "Toothache",
    "dental pain": "Toothache",
    
    # Additional Fatigue/Weakness Terms
    "feeling weak": "Asthenia",
    "weakness": "Asthenia",
    "no energy": "Fatigue",
    "low energy": "Fatigue",
    "exhausted": "Fatigue",
    "worn out": "Fatigue",
    "drained": "Fatigue",
    "can't get out of bed": "Fatigue",
    "muscle weakness": "Muscle weakness",
    "weak muscles": "Muscle weakness",
    "can't lift things": "Muscle weakness",
    
    # Additional Respiratory Terms
    "can't breathe": "Dyspnoea",
    "breathing problems": "Dyspnoea",
    "short of breath": "Dyspnoea",
    "out of breath": "Dyspnoea",
    "breathless": "Dyspnoea",
    "gasping": "Dyspnoea",
    "wheezing": "Wheezing",
    "chest congestion": "Chest discomfort",
    "phlegm": "Sputum increased",
    "sputum increased": "Sputum increased",
    "coughing up phlegm": "Sputum increased",
    "runny nose": "Rhinorrhoea",
    "rhinorrhoea": "Rhinorrhoea",
    "stuffy nose": "Nasal congestion",
    "nasal congestion": "Nasal congestion",
    "congested": "Nasal congestion",
    "sneezing": "Sneezing",
    
    # Additional GI Terms
    "gas": "Flatulence",
    "gassy": "Flatulence",
    "bloating": "Abdominal distension",
    "bloated": "Abdominal distension",
    "stomach bloating": "Abdominal distension",
    "belly bloating": "Abdominal distension",
    "cramps": "Abdominal pain",
    "stomach cramps": "Abdominal pain",
    "belly cramps": "Abdominal pain",
    "cramping": "Abdominal pain",
    "loose stools": "Diarrhoea",
    "watery stools": "Diarrhoea",
    "runny stools": "Diarrhoea",
    "can't go": "Constipation",
    "hard stools": "Constipation",
    "straining": "Constipation",
    "blood in stool": "Haematochezia",
    "haematochezia": "Haematochezia",
    "rectal bleeding": "Haematochezia",
    "black stools": "Melena",
    "melena": "Melena",
    
    # Additional Vision Terms
    "blurry": "Vision blurred",
    "can't see clearly": "Vision blurred",
    "double vision": "Diplopia",
    "diplopia": "Diplopia",
    "seeing double": "Diplopia",
    "eye pain": "Eye pain",
    "sore eyes": "Eye pain",
    "dry eyes": "Dry eye",
    "eyes dry": "Dry eye",
    "red eyes": "Conjunctivitis",
    "pink eye": "Conjunctivitis",
    "conjunctivitis": "Conjunctivitis",
    "eye infection": "Conjunctivitis",
    "sensitivity to light": "Photophobia",
    "photophobia": "Photophobia",
    "light hurts eyes": "Photophobia",
    
    # Additional Blood/Hematologic Terms
    "bruising easily": "Contusion",
    "easy bruising": "Contusion",
    "bruises": "Contusion",
    "black and blue": "Contusion",
    "bleeding easily": "Haemorrhage",
    "bleeds a lot": "Haemorrhage",
    "nosebleeds": "Epistaxis",
    "epistaxis": "Epistaxis",
    "nose bleeding": "Epistaxis",
    "bleeding gums": "Gingival bleeding",
    "gingival bleeding": "Gingival bleeding",
    "gums bleeding": "Gingival bleeding",
    "heavy periods": "Menorrhagia",
    "menorrhagia": "Menorrhagia",
    "heavy menstrual bleeding": "Menorrhagia",
    "periods too heavy": "Menorrhagia",
    
    # Additional Liver Terms
    "yellow skin": "Jaundice",
    "jaundice": "Jaundice",
    "yellow eyes": "Jaundice",
    "yellowing": "Jaundice",
    "liver problems": "Hepatic function abnormal",
    "liver issues": "Hepatic function abnormal",
    "elevated liver enzymes": "Hepatic enzyme increased",
    "liver enzymes high": "Hepatic enzyme increased",
    "alt high": "Alanine aminotransferase increased",
    "ast high": "Aspartate aminotransferase increased",
    
    # Additional Kidney Terms
    "kidney problems": "Renal impairment",
    "kidney issues": "Renal impairment",
    "kidney damage": "Renal impairment",
    "decreased urine": "Oliguria",
    "oliguria": "Oliguria",
    "not urinating": "Anuria",
    "anuria": "Anuria",
    "blood in urine": "Haematuria",
    "haematuria": "Haematuria",
    "urine with blood": "Haematuria",
    "protein in urine": "Proteinuria",
    "proteinuria": "Proteinuria",
    
    # Additional Endocrine/Metabolic Terms
    "low blood sugar": "Hypoglycaemia",
    "blood sugar low": "Hypoglycaemia",
    "sugar low": "Hypoglycaemia",
    "shaky": "Tremor",
    "shaking": "Tremor",
    "tremors": "Tremor",
    "high blood sugar": "Hyperglycaemia",
    "blood sugar high": "Hyperglycaemia",
    "sugar high": "Hyperglycaemia",
    "diabetic": "Diabetes mellitus",
    "diabetes": "Diabetes mellitus",
    "thyroid problems": "Thyroid disorder",
    "thyroid issues": "Thyroid disorder",
    "underactive thyroid": "Hypothyroidism",
    "hypothyroidism": "Hypothyroidism",
    "overactive thyroid": "Hyperthyroidism",
    "hyperthyroidism": "Hyperthyroidism",
    
    # Additional Infection Terms
    "infection": "Infection",
    "infected": "Infection",
    "sepsis": "Sepsis",
    "septic": "Sepsis",
    "blood infection": "Sepsis",
    "bacterial infection": "Bacterial infection",
    "viral infection": "Viral infection",
    "fungal infection": "Fungal infection",
    "yeast infection": "Candidiasis",
    "candidiasis": "Candidiasis",
    "thrush": "Candidiasis",
    "cold": "Nasopharyngitis",
    "common cold": "Nasopharyngitis",
    "flu": "Influenza",
    "influenza": "Influenza",
    "fever and chills": "Pyrexia",
    
    # Additional Allergic Reaction Terms
    "allergic": "Hypersensitivity",
    "allergy": "Hypersensitivity",
    "allergic reaction": "Hypersensitivity",
    "reaction to drug": "Hypersensitivity",
    "drug allergy": "Hypersensitivity",
    "severe allergic reaction": "Anaphylactic reaction",
    "anaphylaxis": "Anaphylactic reaction",
    "anaphylactic shock": "Anaphylactic shock",
    "throat closing": "Anaphylactic reaction",
    "can't breathe allergic": "Anaphylactic reaction",
    "swelling allergic": "Angioedema",
    "angioedema": "Angioedema",
    "face swelling allergic": "Angioedema",
    "tongue swelling": "Angioedema",
    
    # Additional Swelling Terms
    "swollen": "Oedema",
    "swelling": "Oedema",
    "puffy": "Oedema",
    "puffiness": "Oedema",
    "fluid retention": "Oedema",
    "retaining water": "Oedema",
    "water retention": "Oedema",
    "swollen feet": "Peripheral swelling",
    "swollen ankles": "Peripheral swelling",
    "swollen legs": "Peripheral swelling",
    "swollen hands": "Peripheral swelling",
    "swollen face": "Face oedema",
    "puffy face": "Face oedema",
    "facial swelling": "Face oedema",
    "ozempic face": "Face oedema",
    "wegovy face": "Face oedema",
    "mounjaro face": "Face oedema",
    
    # Additional Serious Outcome Terms
    "died": "Death",
    "death": "Death",
    "fatal": "Death",
    "passed away": "Death",
    "expired": "Death",
    "hospitalized": "Hospitalisation",
    "hospitalised": "Hospitalisation",
    "hospitalization": "Hospitalisation",
    "hospitalisation": "Hospitalisation",
    "admitted to hospital": "Hospitalisation",
    "er visit": "Emergency room visit",
    "emergency room": "Emergency room visit",
    "went to er": "Emergency room visit",
    "icu": "Intensive care unit",
    "intensive care": "Intensive care unit",
    "life threatening": "Life threatening",
    "life-threatening": "Life threatening",
    "life threatening event": "Life threatening",
    "disability": "Disability",
    "permanent disability": "Disability",
    "birth defect": "Congenital anomaly",
    "congenital defect": "Congenital anomaly",
    
    # Additional Product Use Issues
    "off label use": "Off label use",
    "off-label use": "Off label use",
    "off label": "Off label use",
    "off-label": "Off label use",
    "product use in unapproved indication": "Off label use",
    "unapproved use": "Off label use",
    "wrong indication": "Off label use",
    "incorrect dose administered": "Incorrect dose administered",
    "wrong dose": "Incorrect dose administered",
    "too much": "Overdose",
    "overdose": "Overdose",
    "took too much": "Overdose",
    "accidental overdose": "Overdose",
    "drug ineffective": "Drug ineffective",
    "product ineffective": "Drug ineffective",
    "treatment failure": "Drug ineffective",
    "not working": "Drug ineffective",
    "stopped working": "Drug ineffective",
    "no effect": "Drug ineffective",
    "product quality issue": "Product quality issue",
    "defective product": "Product quality issue",
    "wrong product": "Product substitution error",
    "product substitution error": "Product substitution error",
    "medication error": "Medication error",
    "wrong medication": "Medication error",
    "took wrong drug": "Medication error",
    
    # Additional Musculoskeletal Terms
    "joint stiffness": "Joint stiffness",
    "stiff joints": "Joint stiffness",
    "stiffness": "Muscle stiffness",
    "muscle stiffness": "Muscle stiffness",
    "stiff": "Muscle stiffness",
    "joint pain": "Arthralgia",
    "arthritis": "Arthritis",
    "arthritic": "Arthritis",
    "bone pain": "Bone pain",
    "fracture": "Fracture",
    "broken bone": "Fracture",
    "bone break": "Fracture",
    "osteoporosis": "Osteoporosis",
    "weak bones": "Osteoporosis",
    "bone loss": "Osteoporosis",
    
    # Additional Neurological Terms (expanded)
    "seizure": "Seizure",
    "convulsion": "Seizure",
    "fits": "Seizure",
    "epilepsy": "Epilepsy",
    "epileptic": "Epilepsy",
    "stroke": "Cerebrovascular accident",
    "cva": "Cerebrovascular accident",
    "cerebrovascular accident": "Cerebrovascular accident",
    "brain attack": "Cerebrovascular accident",
    "mini stroke": "Transient ischaemic attack",
    "tia": "Transient ischaemic attack",
    "transient ischaemic attack": "Transient ischaemic attack",
    "numbness": "Paraesthesia",
    "paraesthesia": "Paraesthesia",
    "pins and needles": "Paraesthesia",
    "tingling": "Paraesthesia",
    "tingly": "Paraesthesia",
    "numb": "Paraesthesia",
    "loss of sensation": "Paraesthesia",
    "weakness on one side": "Hemiparesis",
    "hemiparesis": "Hemiparesis",
    "facial droop": "Facial paralysis",
    "facial paralysis": "Facial paralysis",
    "bell's palsy": "Bell's palsy",
    "bells palsy": "Bell's palsy",
    "slurred speech": "Dysarthria",
    "dysarthria": "Dysarthria",
    "trouble speaking": "Dysarthria",
    "tremor": "Tremor",
    "shaking": "Tremor",
    "tremors": "Tremor",
    "parkinsonism": "Parkinsonism",
    "parkinson's": "Parkinson's disease",
    "parkinsons": "Parkinson's disease",
    
    # Additional Terms - General
    "chills": "Chills",
    "shivering": "Chills",
    "shaking chills": "Chills",
    "sweating": "Hyperhidrosis",
    "hyperhidrosis": "Hyperhidrosis",
    "excessive sweating": "Hyperhidrosis",
    "sweating a lot": "Hyperhidrosis",
    "night sweats": "Night sweats",
    "sweating at night": "Night sweats",
    "tinnitus": "Tinnitus",
    "ringing in ears": "Tinnitus",
    "ears ringing": "Tinnitus",
    "hearing loss": "Deafness",
    "deafness": "Deafness",
    "can't hear": "Deafness",
    "loss of hearing": "Deafness",
    "weight loss": "Weight decreased",
    "weight decreased": "Weight decreased",
    "losing weight": "Weight decreased",
    "lost weight": "Weight decreased",
    "unintended weight loss": "Weight decreased",
    "weight gain": "Weight increased",
    "weight increased": "Weight increased",
    "gaining weight": "Weight increased",
    "gained weight": "Weight increased",
    "unintended weight gain": "Weight increased",
    "loss of appetite": "Decreased appetite",
    "decreased appetite": "Decreased appetite",
    "appetite decreased": "Decreased appetite",
    "not hungry": "Decreased appetite",
    "no appetite": "Decreased appetite",
    "increased appetite": "Appetite increased",
    "appetite increased": "Appetite increased",
    "always hungry": "Appetite increased",
    "very hungry": "Appetite increased",
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
    
    # Direct lookup (exact match)
    if term_lower in FREE_MEDDRA_LIKE:
        return FREE_MEDDRA_LIKE[term_lower]
    
    # Partial match - check if any key is contained in the term
    # BUT: Only use partial matching for substantial matches to avoid false positives
    # Prefer longer, more specific matches
    best_match = None
    best_match_length = 0
    
    for synonym, meddra_pt in FREE_MEDDRA_LIKE.items():
        # Only consider synonyms that are at least 5 characters (avoid matching "use", "pain", etc.)
        if len(synonym) < 5:
            continue
            
        # Check if synonym is contained in the term (e.g., "injection site pain" contains "injection site pain")
        if synonym in term_lower:
            # Prefer longer, more specific matches
            if len(synonym) > best_match_length:
                best_match = meddra_pt
                best_match_length = len(synonym)
    
    # Only return partial match if we found a substantial one (at least 8 chars to avoid false positives)
    if best_match and best_match_length >= 8:
        return best_match
    
    # If no match found, return title-cased original (better than lowercase)
    # This prevents incorrect mappings for unknown terms
    return term_str.title()
