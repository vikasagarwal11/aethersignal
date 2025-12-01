"""
Local FAERS Processing Engine (CHUNK 7.8)
Browser-based FAERS file loading and joining for offline processing.
"""
from .faers_local_engine import FaersLocalEngine, create_faers_engine
from .faers_models import FaersTable, FaersJoinedTable
from .faers_validators import validate_faers_csv, detect_faers_table_type
from .faers_schema_definitions import FAERS_REQUIRED_SCHEMAS

# Export loaders (Parts 2 & 3)
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

# Export join engine (Part 4)
try:
    from .faers_join_engine import FaersJoinEngine
    JOIN_ENGINE_AVAILABLE = True
except ImportError:
    JOIN_ENGINE_AVAILABLE = False

# Build __all__ list
__all__ = [
    "FaersLocalEngine",
    "create_faers_engine",
    "FaersTable",
    "FaersJoinedTable",
    "validate_faers_csv",
    "detect_faers_table_type",
    "FAERS_REQUIRED_SCHEMAS",
]

if LOADERS_AVAILABLE:
    __all__.extend([
        "DemoLoader",
        "DrugLoader",
        "ReacLoader",
        "OutcLoader",
        "TherLoader",
        "IndiLoader"
    ])

if JOIN_ENGINE_AVAILABLE:
    __all__.append("FaersJoinEngine")

