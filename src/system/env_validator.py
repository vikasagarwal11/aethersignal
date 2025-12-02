"""
Environment Validator - Environment variable checker
"""

import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

REQUIRED = []  # No keys are strictly required - system works without them

OPTIONAL = [
    "OPENAI_API_KEY",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "GPU_MODE",
    "LOG_LEVEL",
    "CONFIG_PATH",
    "REDDIT_CLIENT_ID",
    "REDDIT_SECRET",
    "X_API_KEY",
    "PUBMED_API_KEY",
    "EUDRA_API_KEY",
    "HUMAN_API_KEY",
    "METRIPORT_KEY",
    "DRUGBANK_API_KEY",
    "VIGIBASE_KEY"
]


def validate_env() -> Dict[str, Any]:
    """
    Validate environment variables.
    
    Returns:
        Validation results dictionary
    """
    results = {
        "required": {},
        "optional": {},
        "missing_required": [],
        "missing_optional": [],
        "status": "OK"
    }
    
    # Check required
    for var in REQUIRED:
        value = os.getenv(var)
        if value:
            results["required"][var] = "✅ Set"
        else:
            results["required"][var] = "❌ Missing"
            results["missing_required"].append(var)
            results["status"] = "ERROR"
    
    # Check optional
    for var in OPTIONAL:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var or "PASSWORD" in var:
                results["optional"][var] = f"✅ Set (****{value[-4:]})"
            else:
                results["optional"][var] = f"✅ Set ({value})"
        else:
            results["optional"][var] = "⚠️ Not set (optional)"
            results["missing_optional"].append(var)
    
    return results


def get_env_status() -> str:
    """
    Get environment status as formatted string.
    
    Returns:
        Formatted status string
    """
    validation = validate_env()
    
    lines = ["Environment Variable Status:\n"]
    
    if validation["required"]:
        lines.append("Required Variables:")
        for var, status in validation["required"].items():
            lines.append(f"  {var}: {status}")
        lines.append("")
    
    if validation["missing_required"]:
        lines.append(f"⚠️ WARNING: Missing critical env vars: {', '.join(validation['missing_required'])}")
        lines.append("")
    
    lines.append("Optional Variables:")
    for var, status in validation["optional"].items():
        lines.append(f"  {var}: {status}")
    
    return "\n".join(lines)


def print_env_status():
    """Print environment status to console."""
    status = get_env_status()
    print(status)
    logger.info("Environment validation completed")


def check_env_on_startup():
    """
    Check environment on startup and log warnings.
    Should be called at application startup.
    """
    validation = validate_env()
    
    if validation["missing_required"]:
        logger.warning(f"Missing required env vars: {validation['missing_required']}")
    
    # Log optional missing vars at debug level
    if validation["missing_optional"]:
        logger.debug(f"Optional env vars not set: {len(validation['missing_optional'])}")
    
    return validation["status"] == "OK"

