"""
FAERS Loader Base Class (CHUNK 7.8 - Part 1)
Base class for loading FAERS CSV files into lightweight table models.

This is the foundation that all specific loaders (DEMO, DRUG, etc.) depend on.
Compatible with Pyodide for browser-based processing.
"""
import csv
from io import StringIO
from typing import Dict, Any, Optional

from .faers_models import FaersTable
from .faers_validators import validate_faers_csv, validate_faers_file_structure


class FaersLoaderBase:
    """
    Base class for loading FAERS CSV files.
    
    Handles:
    - CSV parsing
    - Schema validation
    - Lightweight table creation
    - Error handling
    """
    
    def __init__(self, table_name: str):
        """
        Initialize loader for specific FAERS table type.
        
        Args:
            table_name: FAERS table type (e.g., "DEMO", "DRUG", "REAC")
        """
        self.table_name = table_name.upper()
    
    def load_csv(self, file_bytes: bytes, validate: bool = True) -> FaersTable:
        """
        Load a FAERS CSV into a lightweight FaersTable model.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with loaded data
            
        Raises:
            ValueError: If validation fails
        """
        # Decode bytes to text
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise ValueError(f"Failed to decode CSV file: {str(e)}")
        
        # Parse CSV
        try:
            reader = csv.DictReader(StringIO(text))
            headers = reader.fieldnames or []
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        # Validate headers
        if validate:
            is_valid, error = validate_faers_csv(self.table_name, headers)
            if not is_valid:
                raise ValueError(f"Invalid FAERS file: {error}")
        
        # Create table and load rows
        table = FaersTable(self.table_name)
        sample_rows = []
        
        for i, row in enumerate(reader):
            # Clean row (remove None values, normalize keys)
            cleaned_row = {}
            for key, value in row.items():
                if key:
                    cleaned_key = key.strip()
                    cleaned_row[cleaned_key] = value.strip() if value else ""
            
            table.add_row(cleaned_row)
            
            # Store first few rows for structure validation
            if i < 10:
                sample_rows.append(cleaned_row)
        
        # Validate structure
        if validate and sample_rows:
            is_valid, error = validate_faers_file_structure(self.table_name, sample_rows)
            if not is_valid:
                raise ValueError(f"Invalid file structure: {error}")
        
        return table
    
    def load_from_dict(self, data: Dict[str, Any]) -> FaersTable:
        """
        Load table from dictionary (for serialized data).
        
        Args:
            data: Dictionary with 'name' and 'rows' keys
            
        Returns:
            FaersTable instance
        """
        table = FaersTable(data.get("name", self.table_name))
        
        rows = data.get("rows", [])
        for row in rows:
            table.add_row(row)
        
        return table
    
    def get_table_name(self) -> str:
        """Get table name."""
        return self.table_name

