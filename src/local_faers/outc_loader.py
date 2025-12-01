"""
FAERS OUTC Loader (CHUNK 7.8 - Part 2)
Loads OUTC (Outcomes) table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class OutcLoader(FaersLoaderBase):
    """
    Loader for FAERS OUTC (Outcomes) table.
    
    Contains case outcome information:
    - primaryid, caseid
    - outc_cod (outcome code: DE=death, LT=life-threatening, etc.)
    """
    
    def __init__(self):
        """Initialize OUTC loader."""
        super().__init__("OUTC")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load OUTC table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with OUTC data
        """
        return super().load_csv(file_bytes, validate=validate)

