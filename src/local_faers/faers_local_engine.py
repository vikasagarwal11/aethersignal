"""
FAERS Local Engine (CHUNK 7.8 - Parts 1, 2, 3)
Main orchestrator for local FAERS file loading and joining.

This file becomes the "brain" of local FAERS processing.
- Part 1: Foundation and shell structure
- Parts 2-3: Individual table loaders integration
- Part 4: Join logic (pending)
"""
from typing import Dict, Any, Optional, List
from .faers_models import FaersTable, FaersJoinedTable

# Import all loaders (Parts 2 & 3)
try:
    from .demo_loader import DemoLoader
    from .drug_loader import DrugLoader
    from .reac_loader import ReacLoader
    from .outc_loader import OutcLoader
    from .ther_loader import TherLoader
    from .indi_loader import IndiLoader
    LOADERS_AVAILABLE = True
except ImportError:
    LOADERS_AVAILABLE = False


class FaersLocalEngine:
    """
    Main engine for local FAERS processing.
    
    Handles:
    - Loading multiple FAERS tables (DEMO, DRUG, REAC, etc.)
    - Validating all tables are present
    - Joining tables into flattened case records
    - Providing joined data for local processing
    """
    
    def __init__(self):
        """Initialize FAERS Local Engine."""
        self.tables: Dict[str, FaersTable] = {}  # DEMO, DRUG, REAC, OUTC, etc.
        self.joined: Optional[FaersJoinedTable] = None  # Flattened dataset
        self.load_status: Dict[str, bool] = {}  # Track which tables are loaded
        self.errors: List[str] = []  # Error messages
    
    def load_table(self, table_name: str, file_bytes: bytes, validate: bool = True) -> bool:
        """
        Load a FAERS table from CSV bytes.
        
        Uses specific loader classes (Parts 2 & 3) for each table type.
        
        Args:
            table_name: Table type (e.g., "DEMO", "DRUG", "REAC")
            file_bytes: CSV file content as bytes
            validate: Whether to validate schema
            
        Returns:
            True if successful, False otherwise
        """
        if not LOADERS_AVAILABLE:
            self.errors.append("FAERS loaders not available. Please check imports.")
            return False
        
        # Loader map (Parts 2 & 3)
        loader_map = {
            "DEMO": DemoLoader(),
            "DRUG": DrugLoader(),
            "REAC": ReacLoader(),
            "OUTC": OutcLoader(),
            "THER": TherLoader(),
            "INDI": IndiLoader(),
        }
        
        table_name_upper = table_name.upper()
        
        if table_name_upper not in loader_map:
            error_msg = f"Unsupported FAERS table: {table_name_upper}. Supported: {list(loader_map.keys())}"
            self.errors.append(error_msg)
            self.load_status[table_name_upper] = False
            return False
        
        try:
            loader = loader_map[table_name_upper]
            table = loader.load(file_bytes, validate=validate)
            
            self.tables[table_name_upper] = table
            self.load_status[table_name_upper] = True
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load {table_name_upper}: {str(e)}"
            self.errors.append(error_msg)
            self.load_status[table_name_upper] = False
            return False
    
    def validate_all_tables_present(self, required_tables: Optional[List[str]] = None) -> bool:
        """
        Validate that all required tables are loaded.
        
        Args:
            required_tables: List of required table names.
                           If None, defaults to ["DEMO", "DRUG", "REAC"]
            
        Returns:
            True if all required tables are present, False otherwise
        """
        if required_tables is None:
            required_tables = ["DEMO", "DRUG", "REAC"]
        
        missing = []
        for table_name in required_tables:
            table_name_upper = table_name.upper()
            if table_name_upper not in self.tables or not self.load_status.get(table_name_upper, False):
                missing.append(table_name_upper)
        
        if missing:
            self.errors.append(f"Missing required tables: {missing}")
            return False
        
        return True
    
    def join_all(self) -> bool:
        """
        Join all loaded tables into flattened case records.
        
        Uses FaersJoinEngine to perform the actual joins (Part 4).
        
        Returns:
            True if join successful, False otherwise
        """
        # Validate required tables are present
        if not self.validate_all_tables_present():
            return False
        
        try:
            # Use optimized join engine if available (Part 5)
            try:
                from .faers_join_engine_optimized import FaersJoinEngineOptimized
                join_engine = FaersJoinEngineOptimized(self.tables)
                self.joined = join_engine.join()
                
                # Store performance stats
                if hasattr(join_engine, 'get_performance_stats'):
                    self.join_performance_stats = join_engine.get_performance_stats()
                
                return True
            except ImportError:
                # Fallback to standard join engine
                from .faers_join_engine import FaersJoinEngine
                join_engine = FaersJoinEngine(self.tables)
                self.joined = join_engine.join()
                return True
            
        except Exception as e:
            error_msg = f"Failed to join tables: {str(e)}"
            self.errors.append(error_msg)
            return False
    
    def get_flattened_cases(self) -> Optional[FaersJoinedTable]:
        """
        Get flattened/joined case records.
        
        Returns:
            FaersJoinedTable with all joined cases, or None if not joined yet
        """
        return self.joined
    
    def get_table(self, table_name: str) -> Optional[FaersTable]:
        """
        Get a specific loaded table.
        
        Args:
            table_name: Table name (e.g., "DEMO", "DRUG")
            
        Returns:
            FaersTable instance or None if not loaded
        """
        return self.tables.get(table_name.upper())
    
    def get_load_status(self) -> Dict[str, bool]:
        """
        Get status of all table loads.
        
        Returns:
            Dictionary mapping table names to load status
        """
        return self.load_status.copy()
    
    def get_errors(self) -> List[str]:
        """Get list of error messages."""
        return self.errors.copy()
    
    def clear(self) -> None:
        """Clear all loaded tables and joined data."""
        self.tables = {}
        self.joined = None
        self.load_status = {}
        self.errors = []
    
    def is_ready_for_join(self) -> bool:
        """
        Check if engine is ready to perform join operation.
        
        Returns:
            True if minimum required tables are loaded
        """
        return self.validate_all_tables_present(["DEMO", "DRUG", "REAC"])
    
    def get_loaded_table_names(self) -> List[str]:
        """
        Get list of successfully loaded table names.
        
        Returns:
            List of table names that are loaded
        """
        return [
            name for name, status in self.load_status.items()
            if status
        ]


def create_faers_engine() -> FaersLocalEngine:
    """Factory function to create FAERS Local Engine instance."""
    return FaersLocalEngine()

