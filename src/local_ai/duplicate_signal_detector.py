"""
Local Duplicate Signal Detector (CHUNK 6.26)
Detects duplicate and similar signals/cases in browser-based processing.

Runs fully offline without server dependencies.
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json


# Check for pandas availability
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class LocalDuplicateSignalDetector:
    """
    Local duplicate signal detection engine.
    
    Detects:
    - Duplicate drug-reaction combinations
    - Multiple similar cases
    - Repeated patterns
    - Potential duplicate report submissions
    - Audit-critical duplicate detection
    
    Works with both pandas DataFrames and lightweight list-of-dicts.
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_threshold: Similarity threshold for duplicate detection (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def detect(
        self, 
        data: Any, 
        key_cols: Optional[List[str]] = None,
        min_duplicate_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Detect potential duplicates based on key columns.
        
        Args:
            data: DataFrame or list of dicts with case records
            key_cols: Columns to use for duplicate detection.
                     Default: ["drug_name", "reaction", "AGE", "SEX"]
            min_duplicate_count: Minimum number of duplicates to flag
            
        Returns:
            List of duplicate groups with counts
        """
        if key_cols is None:
            key_cols = ["drug_name", "reaction", "AGE", "SEX"]
        
        # Convert to DataFrame if needed
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            df = data.copy()
            
            # Find actual column names (handle case variations)
            actual_key_cols = []
            for key_col in key_cols:
                # Try multiple variations
                variations = [
                    key_col,
                    key_col.upper(),
                    key_col.lower(),
                    key_col.capitalize(),
                    key_col.replace("_", "").upper(),
                ]
                
                found_col = next((c for c in variations if c in df.columns), None)
                if found_col:
                    actual_key_cols.append(found_col)
            
            if not actual_key_cols:
                return []
            
            # Group by key columns
            grouped = df.groupby(actual_key_cols).size().reset_index(name="COUNT")
            
            # Filter duplicates
            duplicates = grouped[grouped["COUNT"] >= min_duplicate_count].sort_values(
                "COUNT", ascending=False
            )
            
            # Convert to list of dicts
            results = duplicates.to_dict("records")
            
            return results
        
        elif isinstance(data, list):
            # Lightweight duplicate detection for list-of-dicts
            return self._detect_lightweight(data, key_cols, min_duplicate_count)
        
        else:
            return []
    
    def _detect_lightweight(
        self,
        data: List[Dict[str, Any]],
        key_cols: List[str],
        min_duplicate_count: int
    ) -> List[Dict[str, Any]]:
        """
        Lightweight duplicate detection for list-of-dicts.
        """
        # Build groups by key columns
        groups = defaultdict(list)
        
        for case in data:
            # Build key tuple from case
            key_values = []
            
            for key_col in key_cols:
                # Try multiple column name variations
                value = (
                    case.get(key_col) or
                    case.get(key_col.upper()) or
                    case.get(key_col.lower()) or
                    case.get(key_col.capitalize()) or
                    "UNKNOWN"
                )
                key_values.append(str(value))
            
            key_tuple = tuple(key_values)
            groups[key_tuple].append(case)
        
        # Find duplicates
        duplicates = []
        
        for key_tuple, cases in groups.items():
            if len(cases) >= min_duplicate_count:
                # Build result dict
                result = {
                    "COUNT": len(cases),
                }
                
                # Add key column values
                for i, key_col in enumerate(key_cols):
                    result[key_col] = key_tuple[i]
                
                # Add metadata
                result["case_ids"] = [
                    c.get("primaryid") or c.get("PRIMARYID") or str(i)
                    for i, c in enumerate(cases[:10])  # Limit to first 10
                ]
                
                duplicates.append(result)
        
        # Sort by count (descending)
        duplicates.sort(key=lambda x: x.get("COUNT", 0), reverse=True)
        
        return duplicates
    
    def detect_exact_duplicates(
        self,
        data: Any,
        case_id_col: str = "primaryid"
    ) -> List[Dict[str, Any]]:
        """
        Detect exact duplicate cases (same case ID).
        
        Args:
            data: DataFrame or list of dicts
            case_id_col: Column name for case ID
            
        Returns:
            List of duplicate case IDs with counts
        """
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            df = data.copy()
            
            # Find case ID column
            case_col = next(
                (c for c in [
                    case_id_col,
                    case_id_col.upper(),
                    case_id_col.lower(),
                    "PRIMARYID",
                    "primaryid"
                ] if c in df.columns),
                None
            )
            
            if not case_col:
                return []
            
            # Count duplicates
            duplicates = df[case_col].value_counts()
            duplicates = duplicates[duplicates > 1]
            
            results = [
                {
                    "case_id": case_id,
                    "COUNT": count
                }
                for case_id, count in duplicates.items()
            ]
            
            return results
        
        elif isinstance(data, list):
            # Lightweight exact duplicate detection
            case_id_counts = defaultdict(int)
            
            for case in data:
                case_id = (
                    case.get(case_id_col) or
                    case.get(case_id_col.upper()) or
                    case.get("primaryid") or
                    case.get("PRIMARYID")
                )
                
                if case_id:
                    case_id_counts[str(case_id)] += 1
            
            # Find duplicates
            duplicates = [
                {
                    "case_id": case_id,
                    "COUNT": count
                }
                for case_id, count in case_id_counts.items()
                if count > 1
            ]
            
            return duplicates
        
        else:
            return []
    
    def detect_similar_cases(
        self,
        data: Any,
        similarity_fields: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Detect similar cases based on field similarity (lightweight).
        
        Args:
            data: DataFrame or list of dicts
            similarity_fields: Fields to compare for similarity
            max_results: Maximum number of similar case pairs to return
            
        Returns:
            List of similar case pairs
        """
        if similarity_fields is None:
            similarity_fields = ["drug_name", "reaction", "AGE", "SEX"]
        
        # Convert to list of dicts
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            cases = data.to_dict("records")
        elif isinstance(data, list):
            cases = data
        else:
            return []
        
        similar_pairs = []
        
        # Compare all pairs (for small datasets)
        if len(cases) > 1000:
            # For large datasets, use sampling or indexing
            cases = cases[:500]  # Limit comparisons
        
        for i, case1 in enumerate(cases):
            for j, case2 in enumerate(cases[i+1:], start=i+1):
                similarity = self._compute_similarity(case1, case2, similarity_fields)
                
                if similarity >= self.similarity_threshold:
                    similar_pairs.append({
                        "case1_id": case1.get("primaryid") or case1.get("PRIMARYID") or str(i),
                        "case2_id": case2.get("primaryid") or case2.get("PRIMARYID") or str(j),
                        "similarity": similarity,
                        "matching_fields": [
                            field for field in similarity_fields
                            if self._field_match(case1, case2, field)
                        ]
                    })
                    
                    if len(similar_pairs) >= max_results:
                        break
            
            if len(similar_pairs) >= max_results:
                break
        
        # Sort by similarity (descending)
        similar_pairs.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        return similar_pairs[:max_results]
    
    def _compute_similarity(
        self,
        case1: Dict[str, Any],
        case2: Dict[str, Any],
        fields: List[str]
    ) -> float:
        """Compute similarity score between two cases."""
        if not fields:
            return 0.0
        
        matches = sum(
            1 for field in fields
            if self._field_match(case1, case2, field)
        )
        
        return matches / len(fields) if fields else 0.0
    
    def _field_match(
        self,
        case1: Dict[str, Any],
        case2: Dict[str, Any],
        field: str
    ) -> bool:
        """Check if a field matches between two cases."""
        # Try multiple column name variations
        variations = [
            field,
            field.upper(),
            field.lower(),
            field.capitalize(),
        ]
        
        val1 = None
        val2 = None
        
        for var in variations:
            if var in case1:
                val1 = case1[var]
            if var in case2:
                val2 = case2[var]
        
        if val1 is None or val2 is None:
            return False
        
        # String comparison (case-insensitive)
        return str(val1).strip().lower() == str(val2).strip().lower()

