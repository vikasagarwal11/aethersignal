"""
FAERS INDI Loader (CHUNK 7.8 - Part 3)
Loads INDI (Indications) table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class IndiLoader(FaersLoaderBase):
    """
    Loader for FAERS INDI (Indications) table.
    
    Contains indication information:
    - primaryid, caseid
    - indi_pt (indication Preferred Term from MedDRA)
    """
    
    def __init__(self):
        """Initialize INDI loader."""
        super().__init__("INDI")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load INDI table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with INDI data
        """
        return super().load_csv(file_bytes, validate=validate)

