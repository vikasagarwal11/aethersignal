"""
FAERS Data Models (CHUNK 7.8 - Part 1)
Lightweight in-browser data models for FAERS tables.

Uses Python lists + dicts instead of pandas DataFrames for:
- Faster processing
- Lower memory usage
- Browser compatibility
- Pyodide-friendly operations
"""
from typing import List, Dict, Any, Optional


class FaersTable:
    """
    Generic FAERS table structure (list of dict rows).
    
    Lightweight alternative to pandas DataFrame for browser-based processing.
    """
    
    def __init__(self, name: str, rows: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize FAERS table.
        
        Args:
            name: Table name (e.g., "DEMO", "DRUG", "REAC")
            rows: Optional list of row dictionaries
        """
        self.name = name.upper()
        self.rows = rows or []
        self._index_cache = {}  # For fast lookups
    
    def add_row(self, row: Dict[str, Any]) -> None:
        """Add a row to the table."""
        self.rows.append(row)
        # Clear index cache when adding rows
        self._index_cache = {}
    
    def __len__(self) -> int:
        """Get number of rows."""
        return len(self.rows)
    
    def get_rows_by_key(self, key_column: str, key_value: Any) -> List[Dict[str, Any]]:
        """
        Get all rows matching a key-value pair (for joins).
        
        Handles case-insensitive column name matching (e.g., "primaryid", "PRIMARYID").
        
        Args:
            key_column: Column name to match (e.g., "primaryid")
            key_value: Value to match
            
        Returns:
            List of matching row dictionaries
        """
        # Use cache for repeated lookups
        cache_key = f"{key_column}:{key_value}"
        if cache_key in self._index_cache:
            return self._index_cache[cache_key]
        
        # Try multiple column name variations (case-insensitive)
        key_column_lower = key_column.lower()
        key_column_upper = key_column.upper()
        
        matches = []
        for row in self.rows:
            # Check all possible column name variations
            row_value = (
                row.get(key_column) or 
                row.get(key_column_lower) or 
                row.get(key_column_upper) or
                row.get(key_column.capitalize())
            )
            
            if row_value == key_value:
                matches.append(row)
        
        # Cache result (limit cache size)
        if len(self._index_cache) < 1000:
            self._index_cache[cache_key] = matches
        
        return matches
    
    def get_unique_values(self, column: str) -> List[Any]:
        """Get unique values in a column."""
        values = set()
        for row in self.rows:
            val = row.get(column)
            if val:
                values.add(val)
        return list(values)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert table to dictionary for serialization.
        
        Returns:
            Dictionary representation of the table
        """
        return {
            "name": self.name,
            "row_count": len(self.rows),
            "rows": self.rows[:1000]  # Limit to first 1000 for serialization
        }
    
    def clear(self) -> None:
        """Clear all rows and cache."""
        self.rows = []
        self._index_cache = {}


class FaersJoinedTable:
    """
    Flattened/joined FAERS case table.
    
    Result of joining DEMO + DRUG + REAC + OUTC + THER + INDI.
    """
    
    def __init__(self, rows: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize joined table.
        
        Args:
            rows: List of flattened case records
        """
        self.rows = rows or []
    
    def __len__(self) -> int:
        """Get number of cases."""
        return len(self.rows)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "row_count": len(self.rows),
            "rows": self.rows[:1000]  # Limit for serialization
        }

