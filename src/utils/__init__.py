"""
Utils Module - Utility functions and helpers
"""

from .config_loader import load_config, save_config, DEFAULT_CONFIG

# Import functions from parent utils.py file (avoid circular import)
# Note: src/utils.py is a file, src/utils/ is a directory
# We need to import from the file, not create a circular import
import sys
import os
import importlib.util

# Get path to utils.py file (in parent src/ directory)
_current_file = os.path.abspath(__file__)
_utils_dir = os.path.dirname(_current_file)  # src/utils/
_src_dir = os.path.dirname(_utils_dir)  # src/
_utils_file_path = os.path.join(_src_dir, "utils.py")  # src/utils.py

if os.path.exists(_utils_file_path):
    try:
        spec = importlib.util.spec_from_file_location("_utils_file_module", _utils_file_path)
        _utils_file_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_utils_file_module)
        
        # Import functions from the module
        normalize_text = getattr(_utils_file_module, "normalize_text", None)
        map_to_meddra_pt = getattr(_utils_file_module, "map_to_meddra_pt", None)
        parse_date = getattr(_utils_file_module, "parse_date", None)
        extract_age = getattr(_utils_file_module, "extract_age", None)
        safe_divide = getattr(_utils_file_module, "safe_divide", None)
        clean_drug_name = getattr(_utils_file_module, "clean_drug_name", None)
    except Exception as e:
        # Fallback stubs if import fails
        def normalize_text(text): 
            return str(text).strip().lower() if text else ""
        def map_to_meddra_pt(term): 
            return term
        parse_date = None
        extract_age = None
        safe_divide = None
        clean_drug_name = None
else:
    # Fallback stubs if utils.py doesn't exist
    def normalize_text(text): 
        return str(text).strip().lower() if text else ""
    def map_to_meddra_pt(term): 
        return term
    parse_date = None
    extract_age = None
    safe_divide = None
    clean_drug_name = None

__all__ = [
    "load_config",
    "save_config",
    "DEFAULT_CONFIG",
    "normalize_text",
    "map_to_meddra_pt",
    "parse_date",
    "extract_age",
    "safe_divide",
    "clean_drug_name"
]

