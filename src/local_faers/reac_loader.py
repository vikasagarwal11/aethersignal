"""
FAERS REAC Loader (CHUNK 7.8 - Part 2)
Loads REAC (Reactions) table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class ReacLoader(FaersLoaderBase):
    """
    Loader for FAERS REAC (Reactions) table.
    
    Contains adverse reaction information:
    - primaryid, caseid
    - pt (Preferred Term from MedDRA)
    """
    
    def __init__(self):
        """Initialize REAC loader."""
        super().__init__("REAC")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load REAC table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with REAC data
        """
        return super().load_csv(file_bytes, validate=validate)

