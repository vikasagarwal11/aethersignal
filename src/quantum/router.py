"""
Hybrid Quantum/Classical Router

Automatically selects quantum or classical implementation based on:
- Framework availability
- Data size
- Configuration preferences
- Performance requirements
"""

from typing import Callable, Any, Optional, Dict
import time
import logging
from functools import wraps

from src.quantum.config import get_config

logger = logging.getLogger(__name__)


class QuantumRouter:
    """Router for automatic quantum/classical selection."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize router with optional custom configuration."""
        from src.quantum.config import QuantumConfig
        self.config = QuantumConfig(config) if config else get_config()
    
    def should_use_quantum(self, data_size: int, operation: str = "general") -> bool:
        """Check if quantum should be used for this operation."""
        return self.config.should_use_quantum(data_size, operation)
    
    def execute(
        self,
        operation: str,
        data_size: int,
        quantum_func: Callable,
        classical_func: Callable,
        force_quantum: bool = False,
        force_classical: bool = False,
        **kwargs
    ) -> Any:
        """
        Execute operation with automatic quantum/classical selection.
        
        Args:
            operation: Operation name (for logging)
            data_size: Size of input data
            quantum_func: Quantum implementation function
            classical_func: Classical fallback function
            force_quantum: Force quantum (if available)
            force_classical: Force classical
            **kwargs: Arguments to pass to functions
        
        Returns:
            Result from quantum or classical function
        """
        # Force classical
        if force_classical or self.config.config.get("force_classical", False):
            if self.config.config["logging"]["log_quantum_usage"]:
                logger.debug(f"{operation}: Forced classical")
            return classical_func(**kwargs)
        
        # Check if quantum should be used
        use_quantum = force_quantum or self.should_use_quantum(data_size, operation)
        
        if not use_quantum:
            if self.config.config["logging"]["log_quantum_usage"]:
                logger.debug(f"{operation}: Using classical (data_size={data_size})")
            return classical_func(**kwargs)
        
        # Try quantum with timeout
        timeout = self.config.get_timeout()
        start_time = time.time()
        
        try:
            if self.config.config["logging"]["log_quantum_usage"]:
                logger.info(f"{operation}: Attempting quantum (data_size={data_size})")
            
            result = quantum_func(**kwargs)
            
            elapsed = time.time() - start_time
            if self.config.config["logging"]["log_quantum_usage"]:
                logger.info(f"{operation}: Quantum completed in {elapsed:.2f}s")
            
            return result
        
        except ImportError as e:
            # Framework not available
            if self.config.config["logging"]["log_fallbacks"]:
                logger.warning(f"{operation}: Quantum framework not available, using classical: {e}")
            return classical_func(**kwargs)
        
        except Exception as e:
            # Quantum execution error
            elapsed = time.time() - start_time
            if elapsed > timeout:
                if self.config.config["logging"]["log_fallbacks"]:
                    logger.warning(f"{operation}: Quantum timeout ({elapsed:.2f}s), using classical")
            else:
                if self.config.config["logging"]["log_fallbacks"]:
                    logger.warning(f"{operation}: Quantum error, using classical: {e}")
            
            return classical_func(**kwargs)


def quantum_route(operation: str, data_size_attr: str = "data_size"):
    """
    Decorator for automatic quantum/classical routing.
    
    Usage:
        @quantum_route("clustering", data_size_attr="n_cases")
        def cluster_cases(features, n_cases, ...):
            # Implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            router = QuantumRouter()
            
            # Get data size from kwargs or args
            if data_size_attr in kwargs:
                data_size = kwargs[data_size_attr]
            else:
                # Try to get from first positional arg (if it's a size)
                data_size = len(args[0]) if args and hasattr(args[0], "__len__") else 100
            
            # Check if quantum should be used
            if router.should_use_quantum(data_size, operation):
                # Try quantum version (assumes quantum_func is available)
                try:
                    # This would need to be implemented per function
                    return func(*args, **kwargs, use_quantum=True)
                except Exception as e:
                    logger.warning(f"{operation}: Quantum failed, using classical: {e}")
                    return func(*args, **kwargs, use_quantum=False)
            else:
                return func(*args, **kwargs, use_quantum=False)
        
        return wrapper
    return decorator

