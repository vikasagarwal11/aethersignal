"""
Enhanced Drug Name Normalization and Fuzzy Matching for AetherSignal.
Handles brand names, generic names, misspellings, abbreviations, and multi-drug combinations.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
from collections import defaultdict

from src.utils import normalize_text, clean_drug_name

# Try to use rapidfuzz for better performance, fallback to simple matching
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


# Common drug name variations and abbreviations
DRUG_ABBREVIATIONS = {
    'asp': 'aspirin',
    'acet': 'acetaminophen',
    'ibu': 'ibuprofen',
    'met': 'metformin',
    'lis': 'lisinopril',
    'aml': 'amlodipine',
    'ome': 'omeprazole',
    'sim': 'simvastatin',
    'lev': 'levothyroxine',
    'amlod': 'amlodipine',
    'metf': 'metformin',
    'pred': 'prednisone',
    'predn': 'prednisone',
    'acyc': 'acyclovir',
    'acy': 'acyclovir',
    'acycl': 'acyclovir',
}

# Common brand-to-generic mappings (extended list - top 200+ drugs)
BRAND_TO_GENERIC = {
    # Pain relievers / NSAIDs
    'tylenol': 'acetaminophen',
    'advil': 'ibuprofen',
    'motrin': 'ibuprofen',
    'aleve': 'naproxen',
    'naprosyn': 'naproxen',
    'bayer': 'aspirin',
    'excedrin': 'aspirin',
    'ecotrin': 'aspirin',
    'aspirin': 'aspirin',
    'acetaminophen': 'acetaminophen',
    'ibuprofen': 'ibuprofen',
    'naproxen': 'naproxen',
    'celebrex': 'celecoxib',
    'mobic': 'meloxicam',
    'voltaren': 'diclofenac',
    'indocin': 'indomethacin',
    
    # Statins (cholesterol)
    'lipitor': 'atorvastatin',
    'zocor': 'simvastatin',
    'crestor': 'rosuvastatin',
    'pravachol': 'pravastatin',
    'lescol': 'fluvastatin',
    'mevacor': 'lovastatin',
    
    # Cardiovascular
    'norvasc': 'amlodipine',
    'prinivil': 'lisinopril',
    'zestril': 'lisinopril',
    'cozaar': 'losartan',
    'diovan': 'valsartan',
    'benicar': 'olmesartan',
    'micardis': 'telmisartan',
    'toprol': 'metoprolol',
    'lopressor': 'metoprolol',
    'tenormin': 'atenolol',
    'coreg': 'carvedilol',
    'lasix': 'furosemide',
    'plavix': 'clopidogrel',
    'brilinta': 'ticagrelor',
    'effient': 'prasugrel',
    'coumadin': 'warfarin',
    'eliquis': 'apixaban',
    'xarelto': 'rivaroxaban',
    'pradaxa': 'dabigatran',
    'lisinopril': 'lisinopril',
    'amlodipine': 'amlodipine',
    'metoprolol': 'metoprolol',
    'atenolol': 'atenolol',
    'losartan': 'losartan',
    'valsartan': 'valsartan',
    'furosemide': 'furosemide',
    'hydrochlorothiazide': 'hydrochlorothiazide',
    'clopidogrel': 'clopidogrel',
    'warfarin': 'warfarin',
    
    # GI / Antacids
    'nexium': 'esomeprazole',
    'prilosec': 'omeprazole',
    'prevacid': 'lansoprazole',
    'protonix': 'pantoprazole',
    'aciphex': 'rabeprazole',
    'zantac': 'ranitidine',
    'pepcid': 'famotidine',
    'tagamet': 'cimetidine',
    'omeprazole': 'omeprazole',
    'esomeprazole': 'esomeprazole',
    'lansoprazole': 'lansoprazole',
    'pantoprazole': 'pantoprazole',
    'ranitidine': 'ranitidine',
    'famotidine': 'famotidine',
    
    # Diabetes
    'glucophage': 'metformin',
    'januvia': 'sitagliptin',
    'actos': 'pioglitazone',
    'avandia': 'rosiglitazone',
    'glipizide': 'glipizide',
    'glyburide': 'glyburide',
    'glimepiride': 'glimepiride',
    'metformin': 'metformin',
    'sitagliptin': 'sitagliptin',
    'pioglitazone': 'pioglitazone',
    'rosiglitazone': 'rosiglitazone',
    'humalog': 'insulin lispro',
    'lantus': 'insulin glargine',
    'novolog': 'insulin aspart',
    'toujeo': 'insulin glargine',
    'tresiba': 'insulin degludec',
    'trulicity': 'dulaglutide',
    'ozempic': 'semaglutide',
    'wegovy': 'semaglutide',
    'mounjaro': 'tirzepatide',
    'victoza': 'liraglutide',
    'byetta': 'exenatide',
    
    # Thyroid
    'synthroid': 'levothyroxine',
    'levoxyl': 'levothyroxine',
    'armour': 'thyroid',
    'unithroid': 'levothyroxine',
    'tirosint': 'levothyroxine',
    'levothyroxine': 'levothyroxine',
    
    # Mental health - Antidepressants
    'zoloft': 'sertraline',
    'prozac': 'fluoxetine',
    'paxil': 'paroxetine',
    'celexa': 'citalopram',
    'lexapro': 'escitalopram',
    'wellbutrin': 'bupropion',
    'effexor': 'venlafaxine',
    'cymbalta': 'duloxetine',
    'pristiq': 'desvenlafaxine',
    'sertraline': 'sertraline',
    'fluoxetine': 'fluoxetine',
    'paroxetine': 'paroxetine',
    'citalopram': 'citalopram',
    'escitalopram': 'escitalopram',
    'bupropion': 'bupropion',
    'venlafaxine': 'venlafaxine',
    'duloxetine': 'duloxetine',
    
    # Mental health - Anxiolytics
    'xanax': 'alprazolam',
    'ativan': 'lorazepam',
    'valium': 'diazepam',
    'klonopin': 'clonazepam',
    'alprazolam': 'alprazolam',
    'lorazepam': 'lorazepam',
    'diazepam': 'diazepam',
    'clonazepam': 'clonazepam',
    
    # Sleep aids
    'ambien': 'zolpidem',
    'lunesta': 'eszopiclone',
    'sonata': 'zaleplon',
    'belsomra': 'suvorexant',
    'zolpidem': 'zolpidem',
    'eszopiclone': 'eszopiclone',
    'trazodone': 'trazodone',
    
    # ADHD
    'adderall': 'amphetamine',
    'ritalin': 'methylphenidate',
    'concerta': 'methylphenidate',
    'vyvanse': 'lisdexamfetamine',
    'focalin': 'dexmethylphenidate',
    'strattera': 'atomoxetine',
    'methylphenidate': 'methylphenidate',
    'amphetamine': 'amphetamine',
    
    # ED
    'viagra': 'sildenafil',
    'cialis': 'tadalafil',
    'levitra': 'vardenafil',
    'stendra': 'avanafil',
    'sildenafil': 'sildenafil',
    'tadalafil': 'tadalafil',
    'vardenafil': 'vardenafil',
    
    # Antibiotics
    'amoxil': 'amoxicillin',
    'augmentin': 'amoxicillin clavulanate',
    'zithromax': 'azithromycin',
    'cipro': 'ciprofloxacin',
    'levaquin': 'levofloxacin',
    'vibramycin': 'doxycycline',
    'keflex': 'cephalexin',
    'bactrim': 'sulfamethoxazole trimethoprim',
    'amoxicillin': 'amoxicillin',
    'azithromycin': 'azithromycin',
    'ciprofloxacin': 'ciprofloxacin',
    'levofloxacin': 'levofloxacin',
    'doxycycline': 'doxycycline',
    'cephalexin': 'cephalexin',
    'clindamycin': 'clindamycin',
    'penicillin': 'penicillin',
    
    # Antivirals
    'valtrex': 'valacyclovir',
    'tamiflu': 'oseltamivir',
    'valacyclovir': 'valacyclovir',
    'acyclovir': 'acyclovir',
    'oseltamivir': 'oseltamivir',
    
    # Antifungals
    'diflucan': 'fluconazole',
    'lamisil': 'terbinafine',
    'fluconazole': 'fluconazole',
    'terbinafine': 'terbinafine',
    
    # Steroids
    'prednisone': 'prednisone',
    'prednisolone': 'prednisolone',
    'medrol': 'methylprednisolone',
    'decadron': 'dexamethasone',
    'hydrocortisone': 'hydrocortisone',
    
    # Pain / Neuropathic
    'neurontin': 'gabapentin',
    'lyrica': 'pregabalin',
    'gabapentin': 'gabapentin',
    'pregabalin': 'pregabalin',
    'ultram': 'tramadol',
    'tramadol': 'tramadol',
    
    # Opioids
    'oxycontin': 'oxycodone',
    'percocet': 'oxycodone acetaminophen',
    'vicodin': 'hydrocodone acetaminophen',
    'norco': 'hydrocodone acetaminophen',
    'morphine': 'morphine',
    'fentanyl': 'fentanyl',
    'methadone': 'methadone',
    'suboxone': 'buprenorphine naloxone',
    'oxycodone': 'oxycodone',
    'hydrocodone': 'hydrocodone',
    'buprenorphine': 'buprenorphine',
    
    # Other common
    'albuterol': 'albuterol',
    'ventolin': 'albuterol',
    'proair': 'albuterol',
    'proventil': 'albuterol',
    'singulair': 'montelukast',
    'montelukast': 'montelukast',
    'flonase': 'fluticasone',
    'nasonex': 'mometasone',
    'claritin': 'loratadine',
    'zyrtec': 'cetirizine',
    'allegra': 'fexofenadine',
    'loratadine': 'loratadine',
    'cetirizine': 'cetirizine',
    'fexofenadine': 'fexofenadine',
    'diphenhydramine': 'diphenhydramine',
    'benadryl': 'diphenhydramine',
}

# Common misspellings (can be extended)
COMMON_MISSPELLINGS = {
    'acetylsalicylic': 'aspirin',
    'acetylsalicylate': 'aspirin',
    'asa': 'aspirin',
    'paracetamol': 'acetaminophen',
    'tylenol': 'acetaminophen',
    'advil': 'ibuprofen',
    'motrin': 'ibuprofen',
    'naproxen sodium': 'naproxen',
    'naproxen sodium': 'naproxen',
    'metformin hcl': 'metformin',
    'metformin hydrochloride': 'metformin',
    'lisinopril hctz': 'lisinopril',
    'amlodipine besylate': 'amlodipine',
    'omeprazole magnesium': 'omeprazole',
    'simvastatin': 'simvastatin',
    'atorvastatin calcium': 'atorvastatin',
    'rosuvastatin calcium': 'rosuvastatin',
    'levothyroxine sodium': 'levothyroxine',
    'prednisone': 'prednisone',
    'prednisolone': 'prednisolone',  # Different drug but often confused
}

# Drug name suffixes to normalize
SUFFIX_PATTERNS = [
    (r'\s+hcl\b', ''),  # Remove "HCL" suffix
    (r'\s+hydrochloride\b', ''),
    (r'\s+besylate\b', ''),
    (r'\s+calcium\b', ''),
    (r'\s+magnesium\b', ''),
    (r'\s+sodium\b', ''),
    (r'\s+potassium\b', ''),
    (r'\s+acetate\b', ''),
    (r'\s+citrate\b', ''),
    (r'\s+phosphate\b', ''),
    (r'\s+succinate\b', ''),
    (r'\s+fumarate\b', ''),
    (r'\s+malate\b', ''),
    (r'\s+tartrate\b', ''),
    (r'\s+glucuronide\b', ''),
    (r'\s+hemihydrate\b', ''),
    (r'\s+monohydrate\b', ''),
    (r'\s+dihydrate\b', ''),
    (r'\s+trihydrate\b', ''),
    (r'\s+anhydrous\b', ''),
    (r'\s+\(.*?\)', ''),  # Remove parenthetical info
    (r'\s+\[.*?\]', ''),  # Remove bracketed info
]


def normalize_drug_name(drug: str, aggressive: bool = False) -> str:
    """
    Normalize drug name to canonical form.
    
    Handles:
    - Brand to generic conversion
    - Abbreviation expansion
    - Misspelling correction
    - Suffix removal (HCL, hydrochloride, etc.)
    - Case normalization
    - Whitespace cleanup
    
    Args:
        drug: Drug name string
        aggressive: If True, apply more aggressive normalization (may lose specificity)
        
    Returns:
        Normalized drug name
    """
    if pd.isna(drug) or drug is None:
        return ""
    
    drug_str = str(drug).strip()
    if not drug_str:
        return ""
    
    # Basic cleaning
    drug_str = clean_drug_name(drug_str)
    drug_lower = normalize_text(drug_str)
    
    # Remove common suffixes (e.g., "metformin HCL" -> "metformin")
    for pattern, replacement in SUFFIX_PATTERNS:
        drug_lower = re.sub(pattern, replacement, drug_lower, flags=re.IGNORECASE)
    
    drug_lower = drug_lower.strip()
    
    # Check abbreviations first
    if drug_lower in DRUG_ABBREVIATIONS:
        return DRUG_ABBREVIATIONS[drug_lower].title()
    
    # Check brand-to-generic mapping
    if drug_lower in BRAND_TO_GENERIC:
        return BRAND_TO_GENERIC[drug_lower].title()
    
    # Check misspellings
    if drug_lower in COMMON_MISSPELLINGS:
        return COMMON_MISSPELLINGS[drug_lower].title()
    
    # Aggressive normalization: try partial matches
    if aggressive:
        # Check if any brand/generic is contained in the drug name
        for brand, generic in BRAND_TO_GENERIC.items():
            if brand in drug_lower and len(brand) >= 4:  # Only for substantial matches
                return generic.title()
    
    # Return cleaned, title-cased version
    return drug_str.title()


def split_multi_drug(drug_string: str) -> List[str]:
    """
    Split multi-drug string into individual drugs.
    
    Handles:
    - Semicolon-separated: "DUPIXENT; TACROLIMUS"
    - Comma-separated: "aspirin, ibuprofen"
    - Mixed separators
    
    Args:
        drug_string: String containing one or more drugs
        
    Returns:
        List of individual drug names (normalized)
    """
    if pd.isna(drug_string) or drug_string is None:
        return []
    
    drug_str = str(drug_string).strip()
    if not drug_str:
        return []
    
    # Split by common separators
    drugs = re.split(r'[;,\n]', drug_str)
    
    # Clean and normalize each drug
    normalized_drugs = []
    for drug in drugs:
        drug_clean = drug.strip()
        if drug_clean:
            normalized = normalize_drug_name(drug_clean)
            if normalized:
                normalized_drugs.append(normalized)
    
    return normalized_drugs


def fuzzy_match_drugs(
    drug1: str,
    drug2: str,
    threshold: float = 0.85,
    use_normalization: bool = True
) -> Tuple[bool, float]:
    """
    Fuzzy match two drug names with enhanced normalization.
    Uses rapidfuzz if available for better performance.
    
    Args:
        drug1: First drug name
        drug2: Second drug name
        threshold: Similarity threshold (0-1)
        use_normalization: If True, normalize before matching
        
    Returns:
        Tuple of (is_match: bool, similarity_score: float)
    """
    if not drug1 or not drug2:
        return False, 0.0
    
    # Normalize both drugs
    if use_normalization:
        norm1 = normalize_drug_name(drug1, aggressive=True)
        norm2 = normalize_drug_name(drug2, aggressive=True)
    else:
        norm1 = normalize_text(drug1)
        norm2 = normalize_text(drug2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True, 1.0
    
    # Use rapidfuzz if available (much faster and more accurate)
    if RAPIDFUZZ_AVAILABLE:
        # Use token_sort_ratio for better matching of word order variations
        similarity = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        return similarity >= threshold, similarity
    
    # Fallback to simple matching if rapidfuzz not available
    # Check if one contains the other (after normalization)
    if norm1 in norm2 or norm2 in norm1:
        # Calculate similarity based on length ratio
        shorter = min(len(norm1), len(norm2))
        longer = max(len(norm1), len(norm2))
        similarity = shorter / longer if longer > 0 else 0.0
        return similarity >= threshold, similarity
    
    # Use character-level similarity (simple Jaccard)
    set1 = set(norm1.lower())
    set2 = set(norm2.lower())
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    jaccard_similarity = intersection / union if union > 0 else 0.0
    
    # Word-level similarity
    words1 = set(norm1.lower().split())
    words2 = set(norm2.lower().split())
    
    if words1 or words2:
        word_intersection = len(words1 & words2)
        word_union = len(words1 | words2)
        word_similarity = word_intersection / word_union if word_union > 0 else 0.0
    else:
        word_similarity = 0.0
    
    # Combined similarity (weighted)
    combined_similarity = 0.6 * jaccard_similarity + 0.4 * word_similarity
    
    return combined_similarity >= threshold, combined_similarity


def find_similar_drugs(
    target_drug: str,
    drug_list: List[str],
    threshold: float = 0.85,
    max_results: int = 10
) -> List[Tuple[str, float]]:
    """
    Find similar drugs in a list.
    Uses rapidfuzz.process if available for much better performance.
    
    Args:
        target_drug: Target drug name to match
        drug_list: List of drug names to search
        threshold: Similarity threshold
        max_results: Maximum number of results to return
        
    Returns:
        List of tuples (drug_name, similarity_score), sorted by similarity (descending)
    """
    if not target_drug or not drug_list:
        return []
    
    # Normalize target drug
    target_normalized = normalize_drug_name(target_drug, aggressive=True)
    
    # Use rapidfuzz.process if available (much faster for large lists)
    if RAPIDFUZZ_AVAILABLE:
        # rapidfuzz.process returns list of (drug, score, index)
        results = process.extract(
            target_normalized,
            drug_list,
            scorer=fuzz.token_sort_ratio,
            limit=max_results
        )
        # Convert to (drug, similarity_score) format
        matches = [(drug, score / 100.0) for drug, score, _ in results if (score / 100.0) >= threshold]
        return matches
    
    # Fallback to manual matching
    matches = []
    for drug in drug_list:
        is_match, similarity = fuzzy_match_drugs(target_drug, drug, threshold=threshold)
        if is_match:
            matches.append((drug, similarity))
    
    # Sort by similarity (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches[:max_results]


def normalize_drug_column(df: pd.DataFrame, drug_column: str = 'drug_name') -> pd.DataFrame:
    """
    Normalize drug names in a DataFrame column.
    
    Args:
        df: DataFrame with drug column
        drug_column: Name of drug column
        
    Returns:
        DataFrame with normalized drug names
    """
    if drug_column not in df.columns:
        return df
    
    df_normalized = df.copy()
    
    # Normalize each drug name
    df_normalized[drug_column] = df_normalized[drug_column].apply(
        lambda x: normalize_drug_name(str(x)) if pd.notna(x) else ""
    )
    
    return df_normalized


def create_drug_alias_map(df: pd.DataFrame, drug_column: str = 'drug_name') -> Dict[str, str]:
    """
    Create a mapping of drug name variations to canonical names.
    
    Useful for grouping similar drug names together.
    
    Args:
        df: DataFrame with drug names
        drug_column: Name of drug column
        
    Returns:
        Dictionary mapping variations to canonical names
    """
    if drug_column not in df.columns:
        return {}
    
    # Get unique drug names
    unique_drugs = df[drug_column].dropna().unique()
    
    # Group similar drugs
    alias_map = {}
    canonical_names = set()
    
    for drug in unique_drugs:
        if pd.isna(drug):
            continue
        
        drug_str = str(drug).strip()
        if not drug_str:
            continue
        
        normalized = normalize_drug_name(drug_str, aggressive=True)
        
        # Check if we've seen a similar canonical name
        found_canonical = None
        for canonical in canonical_names:
            is_match, _ = fuzzy_match_drugs(normalized, canonical, threshold=0.9)
            if is_match:
                found_canonical = canonical
                break
        
        if found_canonical:
            alias_map[drug_str] = found_canonical
        else:
            # This is a new canonical name
            canonical_names.add(normalized)
            alias_map[drug_str] = normalized
    
    return alias_map


def group_similar_drugs(
    df: pd.DataFrame,
    drug_column: str = 'drug_name',
    threshold: float = 0.85
) -> pd.DataFrame:
    """
    Group similar drug names together in a DataFrame.
    
    Args:
        df: DataFrame with drug column
        drug_column: Name of drug column
        threshold: Similarity threshold for grouping
        
    Returns:
        DataFrame with new column 'drug_name_normalized' containing grouped names
    """
    if drug_column not in df.columns:
        return df
    
    df_grouped = df.copy()
    
    # Create alias map
    alias_map = create_drug_alias_map(df, drug_column)
    
    # Apply normalization
    df_grouped['drug_name_normalized'] = df_grouped[drug_column].apply(
        lambda x: alias_map.get(str(x), normalize_drug_name(str(x))) if pd.notna(x) else ""
    )
    
    return df_grouped

