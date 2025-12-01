"""
Fallback Manager - Handles fallback logic when models fail
"""

import logging
from typing import Optional, List, Callable

logger = logging.getLogger(__name__)


class FallbackManager:
    """Manages fallback strategies when primary models fail."""
    
    def __init__(self):
        self.fallback_chain = []
    
    def add_fallback(self, fallback_func: Callable):
        """
        Add a fallback function to the chain.
        
        Args:
            fallback_func: Function to call as fallback
        """
        self.fallback_chain.append(fallback_func)
    
    def execute_with_fallback(self, primary_func: Callable, *args, **kwargs) -> Optional[str]:
        """
        Execute primary function with fallback chain.
        
        Args:
            primary_func: Primary function to try first
            *args: Arguments for primary function
            **kwargs: Keyword arguments for primary function
        
        Returns:
            Result from first successful function, or None if all fail
        """
        # Try primary function
        try:
            result = primary_func(*args, **kwargs)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Primary function failed: {e}")
        
        # Try fallback chain
        for fallback_func in self.fallback_chain:
            try:
                result = fallback_func(*args, **kwargs)
                if result:
                    logger.info(f"Fallback succeeded: {fallback_func.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"Fallback {fallback_func.__name__} failed: {e}")
                continue
        
        # All failed
        logger.error("All fallback strategies failed")
        return "Unable to process request. Please try again or check your configuration."

