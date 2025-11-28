"""
Enhanced Cross-Source Deduplication for AetherSignal
Detects duplicates across multiple data sources (FAERS, E2B, Argus, EudraVigilance, etc.)

Uses multiple methods:
1. Exact matching on case identifiers
2. Fuzzy matching on case identifiers
3. Age/sex/event-based matching
4. ML-based duplicate detection (RecordLinkage)
5. Quantum-inspired duplicate detection (enhanced)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import re

from src.utils import normalize_text, safe_divide
from src.quantum_duplicate_detection import (
    quantum_hash,
    quantum_distance,
    detect_duplicates_quantum
)

# Try to import RecordLinkage for ML-based deduplication
try:
    import recordlinkage
    from recordlinkage.preprocessing import clean, phonetic
    from recordlinkage.index import Block, SortedNeighbourhood
    from recordlinkage.compare import String, Exact, Numeric, Date
    RECORDLINKAGE_AVAILABLE = True
except ImportError:
    RECORDLINKAGE_AVAILABLE = False


def detect_cross_source_duplicates(
    df: pd.DataFrame,
    source_column: str = 'source',
    method: str = 'hybrid',
    similarity_threshold: float = 0.85,
    use_ml: bool = True,
    use_quantum: bool = True
) -> Dict:
    """
    Detect duplicates across multiple data sources.
    
    Args:
        df: DataFrame with data from multiple sources
        source_column: Column name indicating data source (e.g., 'FAERS', 'E2B', 'Argus')
        method: Deduplication method ('exact', 'fuzzy', 'ml', 'quantum', 'hybrid')
        similarity_threshold: Threshold for fuzzy matching (0-1)
        use_ml: Whether to use ML-based deduplication (RecordLinkage)
        use_quantum: Whether to use quantum-inspired deduplication
        
    Returns:
        Dictionary with duplicate detection results
    """
    if df.empty:
        return {
            'total_cases': 0,
            'unique_cases': 0,
            'duplicate_cases': 0,
            'duplicate_rate': 0.0,
            'cross_source_duplicates': 0,
            'duplicate_groups': [],
            'method': method
        }
    
    # Ensure source column exists
    if source_column not in df.columns:
        # Try to infer source from other columns
        if 'source' in df.columns:
            source_column = 'source'
        elif 'source_file' in df.columns:
            source_column = 'source_file'
        else:
            # Add default source
            df['source'] = 'unknown'
            source_column = 'source'
    
    # Get unique sources
    sources = df[source_column].unique().tolist() if source_column in df.columns else ['single_source']
    
    if len(sources) == 1:
        # Single source - use standard duplicate detection
        return _detect_single_source_duplicates(df, method, similarity_threshold, use_ml, use_quantum)
    
    # Multi-source deduplication
    return _detect_multi_source_duplicates(
        df, source_column, method, similarity_threshold, use_ml, use_quantum
    )


def _detect_single_source_duplicates(
    df: pd.DataFrame,
    method: str,
    similarity_threshold: float,
    use_ml: bool,
    use_quantum: bool
) -> Dict:
    """Detect duplicates within a single source."""
    if method == 'quantum' and use_quantum:
        return detect_duplicates_quantum(df, similarity_threshold)
    elif method == 'ml' and use_ml and RECORDLINKAGE_AVAILABLE:
        return _detect_duplicates_ml(df, similarity_threshold)
    else:
        # Fallback to classical method
        from src.case_processing import detect_duplicate_cases
        return detect_duplicate_cases(df)


def _detect_multi_source_duplicates(
    df: pd.DataFrame,
    source_column: str,
    method: str,
    similarity_threshold: float,
    use_ml: bool,
    use_quantum: bool
) -> Dict:
    """Detect duplicates across multiple sources."""
    
    # Step 1: Exact matching on case identifiers
    exact_duplicates = _find_exact_duplicates(df, source_column)
    
    # Step 2: Fuzzy matching on case identifiers
    fuzzy_duplicates = []
    if method in ['fuzzy', 'hybrid']:
        fuzzy_duplicates = _find_fuzzy_duplicates(df, source_column, similarity_threshold)
    
    # Step 3: Age/sex/event-based matching
    demographic_duplicates = []
    if method in ['fuzzy', 'hybrid', 'ml']:
        demographic_duplicates = _find_demographic_duplicates(df, source_column, similarity_threshold)
    
    # Step 4: ML-based matching (RecordLinkage)
    ml_duplicates = []
    if method in ['ml', 'hybrid'] and use_ml and RECORDLINKAGE_AVAILABLE:
        ml_duplicates = _find_ml_duplicates(df, source_column, similarity_threshold)
    
    # Step 5: Quantum-inspired matching
    quantum_duplicates = []
    if method in ['quantum', 'hybrid'] and use_quantum:
        quantum_duplicates = _find_quantum_duplicates(df, source_column, similarity_threshold)
    
    # Combine all duplicate groups
    all_duplicate_groups = _merge_duplicate_groups([
        exact_duplicates,
        fuzzy_duplicates,
        demographic_duplicates,
        ml_duplicates,
        quantum_duplicates
    ])
    
    # Calculate statistics
    total_cases = len(df)
    unique_cases = total_cases - sum(len(group) - 1 for group in all_duplicate_groups)
    duplicate_cases = total_cases - unique_cases
    cross_source_count = sum(1 for group in all_duplicate_groups 
                            if len(set(df.loc[group, source_column].values)) > 1)
    
    return {
        'total_cases': total_cases,
        'unique_cases': int(unique_cases),
        'duplicate_cases': int(duplicate_cases),
        'duplicate_rate': round(safe_divide(duplicate_cases, total_cases, 0.0) * 100, 2),
        'cross_source_duplicates': cross_source_count,
        'duplicate_groups': all_duplicate_groups[:100],  # Limit to first 100 groups
        'exact_duplicates': len(exact_duplicates),
        'fuzzy_duplicates': len(fuzzy_duplicates),
        'demographic_duplicates': len(demographic_duplicates),
        'ml_duplicates': len(ml_duplicates),
        'quantum_duplicates': len(quantum_duplicates),
        'method': method
    }


def _find_exact_duplicates(df: pd.DataFrame, source_column: str) -> List[List[int]]:
    """Find exact duplicates based on case identifiers."""
    duplicate_groups = []
    
    # Find case ID column
    case_id_col = None
    for col in ['caseid', 'primaryid', 'isr', 'case_id', 'xevmpd_id']:
        if col in df.columns:
            case_id_col = col
            break
    
    if not case_id_col:
        return []
    
    # Group by case ID and source
    grouped = df.groupby([case_id_col, source_column])
    
    for (case_id, source), group in grouped:
        if len(group) > 1:
            # Multiple rows with same case ID and source
            duplicate_groups.append(group.index.tolist())
    
    # Also check for same case ID across different sources
    cross_source_groups = defaultdict(list)
    for idx, row in df.iterrows():
        case_id = str(row.get(case_id_col, ''))
        if case_id:
            cross_source_groups[case_id].append(idx)
    
    for case_id, indices in cross_source_groups.items():
        if len(indices) > 1:
            # Check if spans multiple sources
            sources = set(df.loc[indices, source_column].values)
            if len(sources) > 1:
                duplicate_groups.append(indices)
    
    return duplicate_groups


def _find_fuzzy_duplicates(
    df: pd.DataFrame,
    source_column: str,
    threshold: float = 0.85
) -> List[List[int]]:
    """Find fuzzy duplicates based on case identifiers."""
    duplicate_groups = []
    
    # Find case ID column
    case_id_col = None
    for col in ['caseid', 'primaryid', 'isr', 'case_id', 'xevmpd_id']:
        if col in df.columns:
            case_id_col = col
            break
    
    if not case_id_col:
        return []
    
    # Get unique case IDs with their indices
    case_id_map = defaultdict(list)
    for idx, row in df.iterrows():
        case_id = str(row.get(case_id_col, '')).strip()
        if case_id and len(case_id) >= 3:
            case_id_map[case_id].append(idx)
    
    # Use quantum distance for fuzzy matching
    case_ids = list(case_id_map.keys())
    
    for i, case_id1 in enumerate(case_ids):
        for case_id2 in case_ids[i+1:]:
            distance = quantum_distance(case_id1, case_id2)
            similarity = 1.0 - distance
            
            if similarity >= threshold:
                # Merge groups
                indices1 = case_id_map[case_id1]
                indices2 = case_id_map[case_id2]
                
                # Check if spans multiple sources
                all_indices = indices1 + indices2
                sources = set(df.loc[all_indices, source_column].values)
                
                if len(sources) > 1 or len(all_indices) > len(indices1):
                    duplicate_groups.append(all_indices)
    
    return duplicate_groups


def _find_demographic_duplicates(
    df: pd.DataFrame,
    source_column: str,
    threshold: float = 0.85
) -> List[List[int]]:
    """Find duplicates based on age, sex, and event matching."""
    duplicate_groups = []
    
    # Required columns
    required_cols = []
    if 'age' in df.columns or 'age_yrs' in df.columns:
        required_cols.append('age' if 'age' in df.columns else 'age_yrs')
    if 'sex' in df.columns or 'gender' in df.columns:
        required_cols.append('sex' if 'sex' in df.columns else 'gender')
    if 'reaction' in df.columns:
        required_cols.append('reaction')
    if 'drug_name' in df.columns:
        required_cols.append('drug_name')
    
    if len(required_cols) < 2:
        return []
    
    # Group by demographic and event characteristics
    for source in df[source_column].unique():
        source_df = df[df[source_column] == source]
        
        # Create signature for each case
        signatures = {}
        for idx, row in source_df.iterrows():
            sig_parts = []
            if 'age' in required_cols or 'age_yrs' in required_cols:
                age = row.get('age') or row.get('age_yrs')
                if pd.notna(age):
                    # Round age to nearest 5 years for matching
                    sig_parts.append(f"age_{int(float(age) // 5) * 5}")
            if 'sex' in required_cols or 'gender' in required_cols:
                sex = str(row.get('sex') or row.get('gender', '')).upper()
                if sex in ['M', 'F']:
                    sig_parts.append(f"sex_{sex}")
            if 'reaction' in required_cols:
                reaction = normalize_text(str(row.get('reaction', '')))
                if reaction:
                    sig_parts.append(f"react_{reaction[:20]}")  # First 20 chars
            if 'drug_name' in required_cols:
                drug = normalize_text(str(row.get('drug_name', '')))
                if drug:
                    sig_parts.append(f"drug_{drug[:20]}")  # First 20 chars
            
            if len(sig_parts) >= 2:
                signature = '|'.join(sig_parts)
                if signature not in signatures:
                    signatures[signature] = []
                signatures[signature].append(idx)
        
        # Find groups with multiple cases
        for signature, indices in signatures.items():
            if len(indices) > 1:
                # Check if any other source has similar cases
                other_sources = df[df[source_column] != source]
                for other_idx, other_row in other_sources.iterrows():
                    other_sig_parts = []
                    if 'age' in required_cols or 'age_yrs' in required_cols:
                        age = other_row.get('age') or other_row.get('age_yrs')
                        if pd.notna(age):
                            other_sig_parts.append(f"age_{int(float(age) // 5) * 5}")
                    if 'sex' in required_cols or 'gender' in required_cols:
                        sex = str(other_row.get('sex') or other_row.get('gender', '')).upper()
                        if sex in ['M', 'F']:
                            other_sig_parts.append(f"sex_{sex}")
                    if 'reaction' in required_cols:
                        reaction = normalize_text(str(other_row.get('reaction', '')))
                        if reaction:
                            other_sig_parts.append(f"react_{reaction[:20]}")
                    if 'drug_name' in required_cols:
                        drug = normalize_text(str(other_row.get('drug_name', '')))
                        if drug:
                            other_sig_parts.append(f"drug_{drug[:20]}")
                    
                    if len(other_sig_parts) >= 2:
                        other_signature = '|'.join(other_sig_parts)
                        # Check similarity
                        if _signature_similarity(signature, other_signature) >= threshold:
                            duplicate_groups.append(indices + [other_idx])
    
    return duplicate_groups


def _signature_similarity(sig1: str, sig2: str) -> float:
    """Calculate similarity between two signatures."""
    parts1 = set(sig1.split('|'))
    parts2 = set(sig2.split('|'))
    
    if not parts1 or not parts2:
        return 0.0
    
    intersection = len(parts1 & parts2)
    union = len(parts1 | parts2)
    
    return intersection / union if union > 0 else 0.0


def _find_ml_duplicates(
    df: pd.DataFrame,
    source_column: str,
    threshold: float = 0.85
) -> List[List[int]]:
    """Find duplicates using ML-based RecordLinkage library."""
    if not RECORDLINKAGE_AVAILABLE:
        return []
    
    duplicate_groups = []
    
    try:
        # Prepare data for RecordLinkage
        # Create indexer
        indexer = recordlinkage.Index()
        
        # Block on source to compare within and across sources
        # For cross-source, we'll compare all pairs
        indexer.full()
        
        # Create comparison object
        compare = recordlinkage.Compare()
        
        # Add comparison rules
        if 'caseid' in df.columns or 'primaryid' in df.columns:
            case_col = 'caseid' if 'caseid' in df.columns else 'primaryid'
            compare.string(case_col, case_col, method='jarowinkler', threshold=threshold, label='case_id')
        
        if 'age' in df.columns or 'age_yrs' in df.columns:
            age_col = 'age' if 'age' in df.columns else 'age_yrs'
            compare.numeric(age_col, age_col, method='gauss', label='age')
        
        if 'sex' in df.columns or 'gender' in df.columns:
            sex_col = 'sex' if 'sex' in df.columns else 'gender'
            compare.exact(sex_col, sex_col, label='sex')
        
        if 'reaction' in df.columns:
            compare.string('reaction', 'reaction', method='jarowinkler', threshold=threshold, label='reaction')
        
        if 'drug_name' in df.columns:
            compare.string('drug_name', 'drug_name', method='jarowinkler', threshold=threshold, label='drug')
        
        # Generate candidate pairs
        candidate_pairs = indexer.index(df)
        
        # Compare
        features = compare.compute(candidate_pairs, df)
        
        # Score pairs (sum of matches)
        scores = features.sum(axis=1)
        
        # Find matches above threshold
        matches = scores[scores >= threshold * len(features.columns)]
        
        # Group matches
        match_groups = defaultdict(set)
        for (idx1, idx2) in matches.index:
            match_groups[idx1].add(idx1)
            match_groups[idx1].add(idx2)
            match_groups[idx2].add(idx1)
            match_groups[idx2].add(idx2)
        
        # Convert to list of lists
        seen = set()
        for group in match_groups.values():
            group_list = sorted(list(group))
            group_tuple = tuple(group_list)
            if group_tuple not in seen and len(group_list) > 1:
                seen.add(group_tuple)
                # Check if spans multiple sources
                try:
                    if source_column in df.columns:
                        sources = set(df.loc[group_list, source_column].values)
                        if len(sources) > 1 or len(group_list) > 1:
                            duplicate_groups.append(group_list)
                    else:
                        # No source column, but still duplicates
                        duplicate_groups.append(group_list)
                except (KeyError, IndexError):
                    # Some indices might be invalid, skip
                    pass
    
    except Exception as e:
        # If ML method fails, return empty list
        pass
    
    return duplicate_groups


def _find_quantum_duplicates(
    df: pd.DataFrame,
    source_column: str,
    threshold: float = 0.85
) -> List[List[int]]:
    """Find duplicates using quantum-inspired methods."""
    duplicate_groups = []
    
    # Use quantum hashing to group similar cases
    case_signatures = {}
    for idx, row in df.iterrows():
        # Create signature from key fields
        sig_parts = []
        
        # Case ID
        for col in ['caseid', 'primaryid', 'isr', 'xevmpd_id']:
            if col in df.columns:
                val = str(row.get(col, '')).strip()
                if val:
                    sig_parts.append(val)
                    break
        
        # Demographics
        if 'age' in df.columns or 'age_yrs' in df.columns:
            age = row.get('age') or row.get('age_yrs')
            if pd.notna(age):
                sig_parts.append(f"age_{int(float(age))}")
        
        if 'sex' in df.columns or 'gender' in df.columns:
            sex = str(row.get('sex') or row.get('gender', '')).upper()
            if sex in ['M', 'F']:
                sig_parts.append(f"sex_{sex}")
        
        # Events
        if 'reaction' in df.columns:
            reaction = normalize_text(str(row.get('reaction', '')))
            if reaction:
                sig_parts.append(f"react_{reaction}")
        
        if 'drug_name' in df.columns:
            drug = normalize_text(str(row.get('drug_name', '')))
            if drug:
                sig_parts.append(f"drug_{drug}")
        
        if sig_parts:
            signature = '|'.join(sig_parts)
            quantum_hash_val = quantum_hash(signature)
            
            if quantum_hash_val not in case_signatures:
                case_signatures[quantum_hash_val] = []
            case_signatures[quantum_hash_val].append(idx)
    
    # Find groups with similar quantum hashes
    hash_groups = defaultdict(list)
    for hash_val, indices in case_signatures.items():
        hash_groups[hash_val].extend(indices)
    
    # Compare cases with same or similar hashes
    for hash_val, indices in hash_groups.items():
        if len(indices) > 1:
            # Check similarity within group
            for i, idx1 in enumerate(indices):
                for idx2 in indices[i+1:]:
                    row1 = df.loc[idx1]
                    row2 = df.loc[idx2]
                    
                    # Create signatures for comparison
                    sig1 = _create_case_signature(row1)
                    sig2 = _create_case_signature(row2)
                    
                    distance = quantum_distance(sig1, sig2)
                    similarity = 1.0 - distance
                    
                    if similarity >= threshold:
                        # Check if spans multiple sources
                        sources = set(df.loc[[idx1, idx2], source_column].values)
                        if len(sources) > 1:
                            # Find or create group
                            found_group = False
                            for group in duplicate_groups:
                                if idx1 in group or idx2 in group:
                                    if idx1 not in group:
                                        group.append(idx1)
                                    if idx2 not in group:
                                        group.append(idx2)
                                    found_group = True
                                    break
                            
                            if not found_group:
                                duplicate_groups.append([idx1, idx2])
    
    return duplicate_groups


def _create_case_signature(row: pd.Series) -> str:
    """Create a signature string from a case row."""
    sig_parts = []
    
    # Case ID
    for col in ['caseid', 'primaryid', 'isr', 'xevmpd_id']:
        if col in row.index:
            val = str(row.get(col, '')).strip()
            if val:
                sig_parts.append(val)
                break
    
    # Demographics
    if 'age' in row.index or 'age_yrs' in row.index:
        age = row.get('age') or row.get('age_yrs')
        if pd.notna(age):
            sig_parts.append(f"age_{int(float(age))}")
    
    if 'sex' in row.index or 'gender' in row.index:
        sex = str(row.get('sex') or row.get('gender', '')).upper()
        if sex in ['M', 'F']:
            sig_parts.append(f"sex_{sex}")
    
    # Events
    if 'reaction' in row.index:
        reaction = normalize_text(str(row.get('reaction', '')))
        if reaction:
            sig_parts.append(f"react_{reaction}")
    
    if 'drug_name' in row.index:
        drug = normalize_text(str(row.get('drug_name', '')))
        if drug:
            sig_parts.append(f"drug_{drug}")
    
    return '|'.join(sig_parts)


def _merge_duplicate_groups(groups_list: List[List[List[int]]]) -> List[List[int]]:
    """Merge overlapping duplicate groups."""
    if not groups_list:
        return []
    
    # Flatten and deduplicate
    all_groups = []
    seen_indices = set()
    
    for groups in groups_list:
        for group in groups:
            if group:
                # Remove duplicates within group
                unique_group = list(dict.fromkeys(group))  # Preserves order
                if len(unique_group) > 1:
                    group_tuple = tuple(sorted(unique_group))
                    if group_tuple not in seen_indices:
                        seen_indices.add(group_tuple)
                        all_groups.append(unique_group)
    
    # Merge overlapping groups
    merged = []
    used = set()
    
    for i, group1 in enumerate(all_groups):
        if i in used:
            continue
        
        current_group = set(group1)
        used.add(i)
        
        # Find all overlapping groups
        changed = True
        while changed:
            changed = False
            for j, group2 in enumerate(all_groups):
                if j in used or j == i:
                    continue
                
                if current_group & set(group2):
                    current_group |= set(group2)
                    used.add(j)
                    changed = True
        
        merged.append(sorted(list(current_group)))
    
    return merged


def remove_duplicates(
    df: pd.DataFrame,
    duplicate_groups: List[List[int]],
    keep_strategy: str = 'first'
) -> pd.DataFrame:
    """
    Remove duplicate cases from DataFrame.
    
    Args:
        df: Original DataFrame
        duplicate_groups: List of duplicate groups (indices)
        keep_strategy: 'first' (keep first occurrence), 'last' (keep last), 
                      'source_priority' (prefer certain sources)
        
    Returns:
        DataFrame with duplicates removed
    """
    if not duplicate_groups:
        return df
    
    # Collect all indices to remove
    indices_to_remove = set()
    
    for group in duplicate_groups:
        if len(group) <= 1:
            continue
        
        if keep_strategy == 'first':
            # Keep first, remove rest
            indices_to_remove.update(group[1:])
        elif keep_strategy == 'last':
            # Keep last, remove rest
            indices_to_remove.update(group[:-1])
        elif keep_strategy == 'source_priority':
            # Prefer certain sources (e.g., FAERS over E2B)
            source_priority = {'FAERS': 1, 'E2B': 2, 'Argus': 3, 'EudraVigilance': 4}
            
            # Get source for each index
            group_with_sources = []
            for idx in group:
                source = df.loc[idx, 'source'] if 'source' in df.columns else 'unknown'
                priority = source_priority.get(source, 99)
                group_with_sources.append((idx, priority, source))
            
            # Sort by priority
            group_with_sources.sort(key=lambda x: x[1])
            
            # Keep first (highest priority), remove rest
            keep_idx = group_with_sources[0][0]
            for idx, _, _ in group_with_sources[1:]:
                indices_to_remove.add(idx)
        else:
            # Default: keep first
            indices_to_remove.update(group[1:])
    
    # Remove duplicates
    df_cleaned = df.drop(index=indices_to_remove).copy()
    
    return df_cleaned


def get_deduplication_report(
    df: pd.DataFrame,
    duplicate_groups: List[List[int]],
    source_column: str = 'source'
) -> Dict:
    """
    Generate a detailed deduplication report.
    
    Args:
        df: Original DataFrame
        duplicate_groups: List of duplicate groups
        source_column: Column name for source
        
    Returns:
        Dictionary with detailed statistics
    """
    if not duplicate_groups:
        return {
            'total_duplicate_groups': 0,
            'total_duplicate_cases': 0,
            'cross_source_groups': 0,
            'source_breakdown': {},
            'examples': []
        }
    
    cross_source_count = 0
    source_breakdown = defaultdict(int)
    examples = []
    
    for group in duplicate_groups[:10]:  # First 10 examples
        if len(group) > 1:
            sources = df.loc[group, source_column].values if source_column in df.columns else ['unknown']
            unique_sources = set(sources)
            
            if len(unique_sources) > 1:
                cross_source_count += 1
            
            for source in unique_sources:
                source_breakdown[source] += 1
            
            # Store example
            if len(examples) < 5:
                example_data = {
                    'indices': group[:5],  # First 5 indices
                    'sources': list(unique_sources),
                    'count': len(group)
                }
                examples.append(example_data)
    
    return {
        'total_duplicate_groups': len(duplicate_groups),
        'total_duplicate_cases': sum(len(g) - 1 for g in duplicate_groups),
        'cross_source_groups': cross_source_count,
        'source_breakdown': dict(source_breakdown),
        'examples': examples
    }

