"""
FAERS THER Loader (CHUNK 7.8 - Part 3)
Loads THER (Therapy) table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class TherLoader(FaersLoaderBase):
    """
    Loader for FAERS THER (Therapy Dates) table.
    
    Contains therapy timing information:
    - primaryid, caseid
    - start_dt (therapy start date)
    - end_dt (therapy end date)
    """
    
    def __init__(self):
        """Initialize THER loader."""
        super().__init__("THER")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load THER table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with THER data
        """
        return super().load_csv(file_bytes, validate=validate)

