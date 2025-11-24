"""
Quantum-inspired duplicate detection for AetherSignal.
Uses quantum-inspired hashing and distance metrics for faster duplicate detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import hashlib
from collections import defaultdict

from src.utils import normalize_text, safe_divide


def quantum_hash(text: str, num_qubits: int = 8) -> int:
    """
    Generate quantum-inspired hash using superposition-like properties.
    
    Uses multiple hash functions and combines them (simulating quantum superposition).
    
    Args:
        text: Text to hash
        num_qubits: Number of hash functions to combine (simulating qubits)
        
    Returns:
        Hash value
    """
    if not text:
        return 0
    
    text_normalized = normalize_text(text)
    
    # Multiple hash functions (simulating quantum superposition)
    hash_values = []
    for i in range(num_qubits):
        # Use different hash seeds
        hash_input = f"{text_normalized}_{i}".encode('utf-8')
        hash_val = int(hashlib.md5(hash_input).hexdigest(), 16)
        hash_values.append(hash_val)
    
    # Combine hashes (XOR simulates quantum entanglement)
    combined_hash = 0
    for h in hash_values:
        combined_hash ^= h
    
    return combined_hash


def quantum_distance(str1: str, str2: str) -> float:
    """
    Calculate quantum-inspired distance between two strings.
    
    Uses quantum-inspired metrics: considers character-level and word-level similarities.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Distance score (0.0 = identical, 1.0 = completely different)
    """
    if not str1 and not str2:
        return 0.0
    if not str1 or not str2:
        return 1.0
    
    s1 = normalize_text(str1)
    s2 = normalize_text(str2)
    
    if s1 == s2:
        return 0.0
    
    # Character-level similarity (Jaccard on character sets)
    set1 = set(s1)
    set2 = set(s2)
    char_intersection = len(set1 & set2)
    char_union = len(set1 | set2)
    char_similarity = safe_divide(char_intersection, char_union, 0.0)
    
    # Word-level similarity
    words1 = set(s1.split())
    words2 = set(s2.split())
    if words1 or words2:
        word_intersection = len(words1 & words2)
        word_union = len(words1 | words2)
        word_similarity = safe_divide(word_intersection, word_union, 0.0)
    else:
        word_similarity = 0.0
    
    # Substring similarity (longest common substring)
    max_common = 0
    for i in range(len(s1)):
        for j in range(i + 1, len(s1) + 1):
            substr = s1[i:j]
            if substr in s2 and len(substr) > max_common:
                max_common = len(substr)
    
    substr_similarity = safe_divide(max_common, max(len(s1), len(s2)), 0.0)
    
    # Quantum-inspired combination (weighted average with non-linear terms)
    distance = 1.0 - (
        0.4 * char_similarity +
        0.4 * word_similarity +
        0.2 * substr_similarity
    )
    
    return max(0.0, min(1.0, distance))


def detect_duplicates_quantum(
    df: pd.DataFrame,
    similarity_threshold: float = 0.95,
    key_fields: Optional[List[str]] = None
) -> Dict:
    """
    Detect duplicate cases using quantum-inspired hashing and distance metrics.
    
    Args:
        df: DataFrame with case data
        similarity_threshold: Threshold for considering cases duplicates (0.0-1.0)
        key_fields: Optional list of fields to use for duplicate detection
        
    Returns:
        Dictionary with duplicate detection results
    """
    if df.empty:
        return {
            'total_cases': 0,
            'unique_cases': 0,
            'duplicate_cases': 0,
            'duplicate_rate': 0.0,
            'duplicate_groups': [],
            'method': 'quantum-inspired'
        }
    
    # Default key fields for duplicate detection
    if key_fields is None:
        key_fields = []
        for col in ['case_id', 'caseid', 'primaryid', 'isr']:
            if col in df.columns:
                key_fields.append(col)
                break
        
        # If no ID column, use combination of drug + reaction + age + sex + date
        if not key_fields:
            key_fields = ['drug_name', 'reaction', 'age', 'sex', 'onset_date']
            key_fields = [f for f in key_fields if f in df.columns]
    
    if not key_fields:
        return {
            'total_cases': len(df),
            'unique_cases': len(df),
            'duplicate_cases': 0,
            'duplicate_rate': 0.0,
            'duplicate_groups': [],
            'method': 'quantum-inspired',
            'error': 'No suitable fields found for duplicate detection'
        }
    
    # Generate quantum hashes for each case
    case_signatures = []
    for idx, row in df.iterrows():
        # Create signature from key fields
        signature_parts = []
        for field in key_fields:
            if field in df.columns:
                val = str(row.get(field, ''))
                signature_parts.append(val)
        
        signature = '|'.join(signature_parts)
        case_hash = quantum_hash(signature)
        
        case_signatures.append({
            'index': idx,
            'signature': signature,
            'hash': case_hash,
            'row': row
        })
    
    # Group by hash (exact duplicates)
    hash_groups = defaultdict(list)
    for case in case_signatures:
        hash_groups[case['hash']].append(case)
    
    # Find exact duplicates
    exact_duplicates = []
    for hash_val, cases in hash_groups.items():
        if len(cases) > 1:
            exact_duplicates.append({
                'hash': hash_val,
                'count': len(cases),
                'indices': [c['index'] for c in cases],
                'type': 'exact'
            })
    
    # Find fuzzy duplicates (similar but not identical)
    fuzzy_duplicates = []
    if similarity_threshold < 1.0:
        # Compare cases with similar hashes (same hash bucket)
        for hash_val, cases in hash_groups.items():
            if len(cases) > 1:
                # Already found as exact duplicates
                continue
            
            # Compare with other cases (simplified: compare with nearby hashes)
            for other_hash, other_cases in hash_groups.items():
                if other_hash == hash_val:
                    continue
                
                # Compare signatures
                for case in cases:
                    for other_case in other_cases:
                        distance = quantum_distance(case['signature'], other_case['signature'])
                        similarity = 1.0 - distance
                        
                        if similarity >= similarity_threshold:
                            fuzzy_duplicates.append({
                                'case1_index': case['index'],
                                'case2_index': other_case['index'],
                                'similarity': similarity,
                                'distance': distance,
                                'type': 'fuzzy'
                            })
    
    # Calculate statistics
    total_cases = len(df)
    exact_duplicate_count = sum(len(d['indices']) - 1 for d in exact_duplicates)  # -1 because one is original
    fuzzy_duplicate_count = len(fuzzy_duplicates)
    total_duplicates = exact_duplicate_count + fuzzy_duplicate_count
    unique_cases = total_cases - exact_duplicate_count  # Fuzzy duplicates don't reduce unique count
    
    return {
        'total_cases': total_cases,
        'unique_cases': int(unique_cases),
        'duplicate_cases': int(total_duplicates),
        'exact_duplicates': int(exact_duplicate_count),
        'fuzzy_duplicates': int(fuzzy_duplicate_count),
        'duplicate_rate': round(safe_divide(total_duplicates, total_cases, 0.0) * 100, 2),
        'duplicate_groups': exact_duplicates[:20],  # Limit to top 20
        'fuzzy_pairs': fuzzy_duplicates[:20],  # Limit to top 20
        'method': 'quantum-inspired',
        'key_fields': key_fields,
        'similarity_threshold': similarity_threshold
    }


def compare_classical_vs_quantum_duplicates(df: pd.DataFrame) -> Dict:
    """
    Compare classical duplicate detection vs quantum-inspired method.
    
    Args:
        df: DataFrame with case data
        
    Returns:
        Dictionary with comparison results
    """
    from src.case_processing import detect_duplicate_cases
    
    # Classical method
    classical_result = detect_duplicate_cases(df)
    
    # Quantum method
    quantum_result = detect_duplicates_quantum(df, similarity_threshold=0.95)
    
    return {
        'classical': classical_result,
        'quantum': quantum_result,
        'comparison': {
            'classical_duplicates': classical_result.get('duplicate_cases', 0),
            'quantum_duplicates': quantum_result.get('duplicate_cases', 0),
            'difference': quantum_result.get('duplicate_cases', 0) - classical_result.get('duplicate_cases', 0),
            'quantum_finds_more': quantum_result.get('duplicate_cases', 0) > classical_result.get('duplicate_cases', 0)
        }
    }

