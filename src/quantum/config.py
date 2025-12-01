"""
Quantum Engine Configuration

Controls quantum framework availability, preferences, and fallback behavior.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Import framework availability from __init__
from src.quantum import QISKIT_AVAILABLE, PENNYLANE_AVAILABLE, OPENQAOA_AVAILABLE

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": True,                    # Master toggle for quantum features
    "prefer_quantum": False,           # Prefer quantum when available (False = prefer classical for stability)
    "force_classical": False,           # Force classical (for testing/debugging)
    "max_data_size_quantum": 1000,      # Max cases for quantum processing (larger = classical)
    "quantum_timeout": 5.0,             # Seconds before fallback to classical
    "frameworks": {
        "qiskit": {
            "enabled": QISKIT_AVAILABLE,
            "backend": "aer_simulator",  # Qiskit simulator backend
            "shots": 1024,               # Number of measurement shots
        },
        "pennylane": {
            "enabled": PENNYLANE_AVAILABLE,
            "device": "default.qubit",   # PennyLane device
            "wires": 4,                  # Number of qubits
        },
        "openqaoa": {
            "enabled": OPENQAOA_AVAILABLE,
            "method": "classical",       # "classical" or "quantum"
        }
    },
    "logging": {
        "log_fallbacks": True,           # Log when falling back to classical
        "log_quantum_usage": True,       # Log when using quantum
    }
}


class QuantumConfig:
    """Quantum engine configuration manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize configuration with defaults or custom config."""
        self.config = {**DEFAULT_CONFIG}
        if config:
            self._merge_config(config)
        self._validate_config()
    
    def _merge_config(self, custom_config: Dict[str, Any]):
        """Merge custom configuration with defaults."""
        if "frameworks" in custom_config:
            for framework, settings in custom_config["frameworks"].items():
                if framework in self.config["frameworks"]:
                    self.config["frameworks"][framework].update(settings)
        self.config.update({k: v for k, v in custom_config.items() if k != "frameworks"})
    
    def _validate_config(self):
        """Validate configuration values."""
        if self.config["max_data_size_quantum"] < 10:
            logger.warning("max_data_size_quantum too small, setting to 10")
            self.config["max_data_size_quantum"] = 10
        
        if self.config["quantum_timeout"] < 1.0:
            logger.warning("quantum_timeout too small, setting to 1.0")
            self.config["quantum_timeout"] = 1.0
    
    def is_quantum_enabled(self) -> bool:
        """Check if quantum features are enabled."""
        return self.config["enabled"] and not self.config["force_classical"]
    
    def is_framework_enabled(self, framework: str) -> bool:
        """Check if a specific framework is enabled."""
        if not self.is_quantum_enabled():
            return False
        return self.config["frameworks"].get(framework, {}).get("enabled", False)
    
    def should_use_quantum(self, data_size: int, operation: str = "general") -> bool:
        """
        Determine if quantum should be used for an operation.
        
        Args:
            data_size: Number of data points/cases
            operation: Type of operation (for future operation-specific logic)
        
        Returns:
            True if quantum should be used, False for classical
        """
        if not self.is_quantum_enabled():
            return False
        
        if self.config["force_classical"]:
            return False
        
        # Data size check
        if data_size > self.config["max_data_size_quantum"]:
            if self.config["logging"]["log_fallbacks"]:
                logger.info(f"Data size {data_size} exceeds quantum limit, using classical")
            return False
        
        # Preference check
        if not self.config["prefer_quantum"]:
            # Only use quantum if explicitly preferred or for small datasets
            return data_size < 100  # Small datasets only
        
        return True
    
    def get_framework_config(self, framework: str) -> Dict[str, Any]:
        """Get configuration for a specific framework."""
        return self.config["frameworks"].get(framework, {})
    
    def get_timeout(self) -> float:
        """Get quantum operation timeout in seconds."""
        return self.config["quantum_timeout"]


# Global configuration instance
_global_config: Optional[QuantumConfig] = None


def get_config() -> QuantumConfig:
    """Get global quantum configuration."""
    global _global_config
    if _global_config is None:
        _global_config = QuantumConfig()
    return _global_config


def set_config(config: Dict[str, Any]):
    """Set global quantum configuration."""
    global _global_config
    _global_config = QuantumConfig(config)

