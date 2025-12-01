"""
FAERS DEMO Loader (CHUNK 7.8 - Part 2)
Loads DEMO (Demographics) table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class DemoLoader(FaersLoaderBase):
    """
    Loader for FAERS DEMO (Demographics) table.
    
    Contains patient demographics:
    - primaryid, caseid
    - sex, age, weight
    - event dates
    - reporter country
    """
    
    def __init__(self):
        """Initialize DEMO loader."""
        super().__init__("DEMO")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load DEMO table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with DEMO data
        """
        return super().load_csv(file_bytes, validate=validate)

