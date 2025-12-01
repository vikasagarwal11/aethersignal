"""
FAERS DRUG Loader (CHUNK 7.8 - Part 2)
Loads DRUG table from FAERS CSV files.
"""
from .faers_loader_base import FaersLoaderBase


class DrugLoader(FaersLoaderBase):
    """
    Loader for FAERS DRUG table.
    
    Contains drug information:
    - primaryid, caseid
    - drug_seq, role_cod (suspect/concomitant)
    - drugname, prod_ai
    - route, dose, dosage form
    """
    
    def __init__(self):
        """Initialize DRUG loader."""
        super().__init__("DRUG")
    
    def load(self, file_bytes: bytes, validate: bool = True):
        """
        Load DRUG table from CSV bytes.
        
        Args:
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema (default: True)
            
        Returns:
            FaersTable instance with DRUG data
        """
        return super().load_csv(file_bytes, validate=validate)

