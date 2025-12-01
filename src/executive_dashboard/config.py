"""
Executive Dashboard Configuration
SuperAdmin-configurable toggles for sources and features.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("configs/executive_config.yaml")

DEFAULT_CONFIG = {
    "sources": {
        "faers": True,
        "social": True,
        "literature": True,
        "clinical_trials": True,
        "openfda": True,
        "pubmed": True,
        "dailymed": True
    },
    "features": {
        "severity_engine": True,
        "quantum_engine": True,
        "mechanism_ai": True,
        "trend_forecast": True,
        "geo_analysis": True,
        "narrative_ai": True,
        "label_intelligence": True,
        "risk_matrix": True
    },
    "display": {
        "default_days_back": 90,
        "trend_periods": [7, 30, 90, 365],
        "max_signals_display": 50
    }
}


def load_config() -> Dict[str, Any]:
    """Load executive dashboard configuration."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
    except Exception as e:
        logger.warning(f"Error loading config: {e}, using defaults")
        return DEFAULT_CONFIG


def save_config(config: Dict[str, Any]):
    """Save executive dashboard configuration."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        logger.error(f"Error saving config: {e}")


def is_source_enabled(source_name: str) -> bool:
    """Check if a data source is enabled."""
    config = load_config()
    return config.get("sources", {}).get(source_name, False)


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    config = load_config()
    return config.get("features", {}).get(feature_name, False)

