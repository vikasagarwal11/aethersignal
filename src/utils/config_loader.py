"""
Global Config Loader - Auto-fallback + Self-healing configuration
"""

import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "system_mode": "MVP",
    "enable_mechanism_ai": True,
    "enable_quantum_scoring": False,
    "enable_literature": True,
    "enable_social": True,
    "enable_faers": True,
    "enable_analytics": True,
    "enable_copilot": True,
    "enable_workflow": True,
    "enable_evidence_governance": True,
    "enable_pricing": False,  # Pricing system toggle (super admin only)
    "api_keys": {},
    "cache_enabled": True,
    "gpu_enabled": False,
    "log_level": "INFO"
}

CONFIG_PATH = os.getenv("CONFIG_PATH", "config/aethersignal_config.json")


def ensure_config_dir():
    """Ensure config directory exists."""
    config_dir = os.path.dirname(CONFIG_PATH)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """
    Load configuration with auto-repair.
    
    Returns:
        Configuration dictionary
    """
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_PATH):
        logger.info(f"Config file not found, creating default at {CONFIG_PATH}")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Ensure api_keys exists
        if "api_keys" not in merged_config:
            merged_config["api_keys"] = {}
        
        return merged_config
        
    except json.JSONDecodeError as e:
        logger.warning(f"Config file corrupted, resetting to defaults: {e}")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logger.error(f"Config load error: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]):
    """
    Save configuration.
    
    Args:
        cfg: Configuration dictionary
    """
    ensure_config_dir()
    
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Config save error: {e}")
        raise


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a single config value.
    
    Args:
        key: Config key
        default: Default value if key not found
    
    Returns:
        Config value or default
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any):
    """
    Set a single config value.
    
    Args:
        key: Config key
        value: Value to set
    """
    config = load_config()
    config[key] = value
    save_config(config)

