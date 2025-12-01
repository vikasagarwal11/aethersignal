"""
FAERS Validators (CHUNK 7.8 - Part 1)
Validates FAERS CSV files to ensure they contain required columns.

Prevents corrupted or invalid files from crashing the join engine.
"""
from typing import Tuple, List, Optional
from .faers_schema_definitions import FAERS_REQUIRED_SCHEMAS


def validate_faers_csv(table_name: str, csv_headers: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that CSV contains required FAERS columns.
    
    Args:
        table_name: FAERS table type (e.g., "DEMO", "DRUG", "REAC")
        csv_headers: List of column names from CSV header row
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False otherwise
        - error_message: Error description if invalid, None if valid
    """
    table_name_upper = table_name.upper()
    required = FAERS_REQUIRED_SCHEMAS.get(table_name_upper)
    
    if not required:
        return False, f"Unknown FAERS table type: {table_name}. Supported types: {list(FAERS_REQUIRED_SCHEMAS.keys())}"
    
    # Normalize headers (lowercase for comparison)
    csv_headers_lower = [h.lower().strip() for h in csv_headers]
    required_lower = [r.lower().strip() for r in required]
    
    # Check for missing required columns
    missing = []
    for req_col in required_lower:
        if req_col not in csv_headers_lower:
            # Try case-insensitive match
            found = any(req_col == h for h in csv_headers_lower)
            if not found:
                missing.append(req_col)
    
    if missing:
        return False, f"Missing required fields for {table_name_upper}: {missing}"
    
    return True, None


def validate_faers_file_structure(table_name: str, sample_rows: List[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate FAERS file structure by checking sample rows.
    
    Args:
        table_name: FAERS table type
        sample_rows: List of first few row dictionaries
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not sample_rows:
        return False, f"No rows found in {table_name} file"
    
    # Check that primary key exists in all rows
    required_schema = FAERS_REQUIRED_SCHEMAS.get(table_name.upper())
    if not required_schema:
        return True, None  # Unknown type, skip validation
    
    primary_key = "primaryid"
    
    for i, row in enumerate(sample_rows[:10]):  # Check first 10 rows
        if primary_key not in row or not row.get(primary_key):
            return False, f"Row {i+1} missing required primary key '{primary_key}'"
    
    return True, None


def detect_faers_table_type(csv_headers: List[str]) -> Optional[str]:
    """
    Auto-detect FAERS table type from CSV headers.
    
    Args:
        csv_headers: List of column names
        
    Returns:
        Detected table type (e.g., "DEMO", "DRUG") or None
    """
    csv_headers_lower = [h.lower().strip() for h in csv_headers]
    
    # Score each table type based on matching columns
    scores = {}
    for table_type, required_cols in FAERS_REQUIRED_SCHEMAS.items():
        required_lower = [r.lower().strip() for r in required_cols]
        matches = sum(1 for col in required_lower if col in csv_headers_lower)
        score = matches / len(required_lower) if required_lower else 0
        scores[table_type] = score
    
    # Return table type with highest score (if > 0.8 match)
    if scores:
        best_match = max(scores.items(), key=lambda x: x[1])
        if best_match[1] >= 0.8:
            return best_match[0]
    
    return None

