"""
Startup Health Checks - Validates system on startup
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def startup_health_check() -> Dict[str, Any]:
    """
    Run startup health checks.
    
    Returns:
        Dictionary with check results
    """
    checks = {
        "logs_dir": False,
        "storage_dir": False,
        "data_dir": False,
        "config_dir": False,
        "python_version": False,
        "required_modules": False,
        "warnings": []
    }
    
    # Check directories
    dirs_to_check = {
        "logs_dir": "logs",
        "storage_dir": "storage",
        "data_dir": "data",
        "config_dir": "config"
    }
    
    for check_name, dir_path in dirs_to_check.items():
        if os.path.isdir(dir_path):
            checks[check_name] = True
            logger.info(f"✔ {check_name} OK")
        else:
            try:
                os.makedirs(dir_path, exist_ok=True)
                checks[check_name] = True
                logger.info(f"✔ {check_name} created")
            except Exception as e:
                checks["warnings"].append(f"Could not create {dir_path}: {e}")
                logger.warning(f"✖ {check_name} missing and could not be created")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 10:
        checks["python_version"] = True
        logger.info(f"✔ Python version OK: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        checks["warnings"].append(f"Python {python_version.major}.{python_version.minor} detected. Python 3.10+ recommended.")
        logger.warning(f"⚠ Python version: {python_version.major}.{python_version.minor}")
    
    # Check required modules
    required_modules = [
        "streamlit",
        "pandas",
        "numpy",
        "plotly"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if not missing_modules:
        checks["required_modules"] = True
        logger.info("✔ Required modules OK")
    else:
        checks["warnings"].append(f"Missing modules: {', '.join(missing_modules)}")
        logger.error(f"✖ Missing required modules: {', '.join(missing_modules)}")
    
    # Check .env file
    if os.path.isfile(".env"):
        logger.info("✔ .env file found")
    else:
        checks["warnings"].append(".env file not found (using defaults)")
        logger.warning("⚠ .env file not found")
    
    # Overall status
    critical_checks = ["logs_dir", "storage_dir", "python_version", "required_modules"]
    all_critical_ok = all(checks.get(c, False) for c in critical_checks)
    
    if all_critical_ok:
        logger.info("✅ Startup health checks passed")
    else:
        logger.warning("⚠️ Some startup checks failed")
    
    return checks


def print_startup_summary():
    """Print startup summary to console."""
    checks = startup_health_check()
    
    print("\n" + "="*50)
    print("AetherSignal Startup Health Check")
    print("="*50)
    
    for check_name, status in checks.items():
        if isinstance(status, bool):
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {check_name}: {status}")
    
    if checks.get("warnings"):
        print("\n⚠️  Warnings:")
        for warning in checks["warnings"]:
            print(f"   - {warning}")
    
    print("="*50 + "\n")

