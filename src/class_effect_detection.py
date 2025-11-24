"""
Class effect detection for AetherSignal.
Identifies drug class patterns (e.g., all ACE inhibitors showing similar reactions).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set
from collections import defaultdict, Counter

from src import signal_stats
from src.utils import normalize_text, safe_divide

# Common drug class mappings (can be extended)
DRUG_CLASSES = {
    # ACE Inhibitors
    "ace_inhibitor": ["lisinopril", "enalapril", "ramipril", "captopril", "fosinopril", "quinapril", "benazepril"],
    # ARBs (Angiotensin Receptor Blockers)
    "arb": ["losartan", "valsartan", "irbesartan", "candesartan", "telmisartan", "olmesartan", "azilsartan"],
    # Beta Blockers
    "beta_blocker": ["metoprolol", "atenolol", "propranolol", "carvedilol", "bisoprolol", "nebivolol", "labetalol"],
    # Statins
    "statin": ["atorvastatin", "simvastatin", "pravastatin", "rosuvastatin", "lovastatin", "fluvastatin", "pitavastatin"],
    # PPIs (Proton Pump Inhibitors)
    "ppi": ["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole", "dexlansoprazole"],
    # SSRIs (Selective Serotonin Reuptake Inhibitors)
    "ssri": ["fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram", "fluvoxamine"],
    # NSAIDs
    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "celecoxib", "meloxicam", "indomethacin", "ketorolac"],
    # Opioids
    "opioid": ["morphine", "oxycodone", "hydrocodone", "fentanyl", "codeine", "tramadol", "methadone"],
    # Antibiotics
    "antibiotic": ["amoxicillin", "azithromycin", "ciprofloxacin", "levofloxacin", "doxycycline", "clindamycin"],
    # Antihistamines
    "antihistamine": ["diphenhydramine", "loratadine", "cetirizine", "fexofenadine", "desloratadine"],
}


def get_drug_class(drug_name: str) -> Optional[str]:
    """
    Identify drug class for a given drug name.
    
    Args:
        drug_name: Drug name
        
    Returns:
        Drug class name or None
    """
    drug_lower = normalize_text(drug_name)
    
    for class_name, drugs in DRUG_CLASSES.items():
        for class_drug in drugs:
            if normalize_text(class_drug) in drug_lower or drug_lower in normalize_text(class_drug):
                return class_name
    
    return None


def detect_class_effects(
    normalized_df: pd.DataFrame,
    reaction: Optional[str] = None,
    min_drugs_in_class: int = 2,
    min_cases_per_drug: int = 3
) -> List[Dict]:
    """
    Detect class effects (reactions common across drug class).
    
    Args:
        normalized_df: Normalized dataset
        reaction: Optional specific reaction to analyze
        min_drugs_in_class: Minimum drugs in class showing the reaction
        min_cases_per_drug: Minimum cases per drug
        
    Returns:
        List of class effect dictionaries
    """
    # Map drugs to classes
    drug_to_class = {}
    class_to_drugs = defaultdict(list)
    
    for drug in normalized_df["drug_name"].unique():
        drug_str = str(drug)
        # Handle multi-drug entries (semicolon-separated)
        for single_drug in drug_str.split(";"):
            single_drug = single_drug.strip()
            if single_drug:
                drug_class = get_drug_class(single_drug)
                if drug_class:
                    drug_to_class[single_drug] = drug_class
                    class_to_drugs[drug_class].append(single_drug)
    
    if not drug_to_class:
        return []
    
    # Filter for reaction if specified
    filtered_df = normalized_df.copy()
    if reaction:
        reaction_mask = filtered_df["reaction"].apply(
            lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
        )
        filtered_df = filtered_df[reaction_mask]
    
    # Analyze each drug class
    class_effects = []
    
    for class_name, drugs_in_class in class_to_drugs.items():
        if len(drugs_in_class) < min_drugs_in_class:
            continue
        
        # Get reactions for all drugs in this class
        class_reactions = Counter()
        drug_reaction_counts = defaultdict(int)
        
        for drug in drugs_in_class:
            drug_mask = filtered_df["drug_name"].apply(
                lambda x: normalize_text(str(drug)) in normalize_text(str(x))
            )
            drug_cases = filtered_df[drug_mask]
            
            if len(drug_cases) < min_cases_per_drug:
                continue
            
            # Count reactions for this drug
            for _, row in drug_cases.iterrows():
                reactions = str(row.get("reaction", "")).split(";")
                for r in reactions:
                    r = r.strip()
                    if r:
                        class_reactions[r] += 1
                        drug_reaction_counts[(drug, r)] += 1
        
        # Find reactions that appear with multiple drugs in the class
        reaction_drug_counts = defaultdict(set)
        for (drug, reaction), count in drug_reaction_counts.items():
            if count >= min_cases_per_drug:
                reaction_drug_counts[reaction].add(drug)
        
        # Class effects: reactions appearing with >= min_drugs_in_class
        for reaction_name, drugs_showing in reaction_drug_counts.items():
            if len(drugs_showing) >= min_drugs_in_class:
                total_cases = class_reactions[reaction_name]
                
                # Calculate class-wide metrics
                class_effect = {
                    "drug_class": class_name,
                    "reaction": reaction_name,
                    "n_drugs_showing": len(drugs_showing),
                    "drugs_in_class": list(drugs_showing),
                    "total_cases": total_cases,
                    "avg_cases_per_drug": float(total_cases / len(drugs_showing)),
                }
                
                # Calculate PRR for class vs. non-class
                class_drug_mask = filtered_df["drug_name"].apply(
                    lambda x: any(normalize_text(d) in normalize_text(str(x)) for d in drugs_showing)
                )
                reaction_mask = filtered_df["reaction"].apply(
                    lambda x: normalize_text(reaction_name) in normalize_text(str(x))
                )
                
                a = (class_drug_mask & reaction_mask).sum()
                b = (class_drug_mask & ~reaction_mask).sum()
                c = (~class_drug_mask & reaction_mask).sum()
                d = (~class_drug_mask & ~reaction_mask).sum()
                
                if a > 0:
                    prr_result = signal_stats.calculate_prr_ror(a, b, c, d)
                    class_effect["class_prr"] = prr_result.get("prr", 0.0)
                    class_effect["class_ror"] = prr_result.get("ror", 0.0)
                
                class_effects.append(class_effect)
    
    # Sort by number of drugs showing the reaction (most common class effects first)
    class_effects.sort(key=lambda x: x["n_drugs_showing"], reverse=True)
    
    return class_effects


def analyze_drug_class_signal(
    normalized_df: pd.DataFrame,
    drug: str,
    reaction: str
) -> Dict:
    """
    Analyze if a drug-reaction signal is part of a class effect.
    
    Args:
        normalized_df: Normalized dataset
        drug: Drug name
        reaction: Reaction name
        
    Returns:
        Dictionary with class effect analysis
    """
    drug_class = get_drug_class(drug)
    
    if not drug_class:
        return {
            "is_class_effect": False,
            "drug_class": None,
            "other_drugs_in_class": [],
            "other_drugs_showing_reaction": [],
            "class_effect_strength": 0.0,
        }
    
    # Get all drugs in this class
    drugs_in_class = DRUG_CLASSES.get(drug_class, [])
    
    # Check which other drugs in class show this reaction
    other_drugs_showing = []
    
    for class_drug in drugs_in_class:
        if normalize_text(class_drug) == normalize_text(drug):
            continue  # Skip the current drug
        
        drug_mask = normalized_df["drug_name"].apply(
            lambda x: normalize_text(str(class_drug)) in normalize_text(str(x))
        )
        reaction_mask = normalized_df["reaction"].apply(
            lambda x: normalize_text(str(reaction)) in normalize_text(str(x))
        )
        
        n_cases = (drug_mask & reaction_mask).sum()
        if n_cases >= 3:  # Minimum threshold
            other_drugs_showing.append({
                "drug": class_drug,
                "n_cases": int(n_cases),
            })
    
    is_class_effect = len(other_drugs_showing) >= 1
    
    # Class effect strength: proportion of class drugs showing the reaction
    class_effect_strength = safe_divide(len(other_drugs_showing), len(drugs_in_class), 0.0)
    
    return {
        "is_class_effect": is_class_effect,
        "drug_class": drug_class,
        "other_drugs_in_class": drugs_in_class,
        "other_drugs_showing_reaction": other_drugs_showing,
        "n_other_drugs_showing": len(other_drugs_showing),
        "class_effect_strength": float(class_effect_strength),
    }

