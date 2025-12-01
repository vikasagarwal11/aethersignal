"""
Safe Executor Layer for Data Source Fetching.
Provides retry logic, timeout handling, and graceful degradation.
Universal fault-tolerance backbone for all data sources.
"""

import logging
import time
import traceback
from typing import Any, Callable, Optional, Union, Dict
from functools import wraps
import platform

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
import requests
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError as RequestsConnectionError
)

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        attempts: int = 3,
        min_wait: int = 1,
        max_wait: int = 10,
        multiplier: int = 2,
        timeout_secs: int = 20,
    ):
        self.attempts = attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
        self.timeout_secs = timeout_secs


class SafeExecutor:
    """
    Executes a callable with retries, exponential backoff, timeouts, and soft-failure.
    Universal fault-tolerance backbone for all data sources.
    """
    
    def __init__(self, source_name: str, retry_config: Optional[RetryConfig] = None):
        """
        Initialize safe executor.
        
        Args:
            source_name: Name of the data source (for logging)
            retry_config: Retry configuration (uses defaults if None)
        """
        self.source_name = source_name
        self.config = retry_config or RetryConfig()
    
    def _log(self, level: str, message: str):
        """Log message with source name prefix."""
        getattr(logger, level.lower())(
            f"[{self.source_name}] {message}"
        )
    
    def with_retry(self, fn: Callable):
        """
        Decorator that adds retry logic to a function.
        
        Args:
            fn: Function to wrap with retry logic
        
        Returns:
            Wrapped function with retry behavior
        """
        @retry(
            stop=stop_after_attempt(self.config.attempts),
            wait=wait_exponential(
                multiplier=self.config.multiplier,
                min=self.config.min_wait,
                max=self.config.max_wait,
            ),
            retry=retry_if_exception_type((
                RequestException,
                Timeout,
                RequestsConnectionError,
                ConnectionError,
                Exception  # Catch all exceptions for maximum safety
            )),
            reraise=True,
        )
        def wrapped(*args, **kwargs):
            self._log("info", f"Executing {fn.__name__} with retry...")
            # Use requests timeout for HTTP calls, or config timeout for others
            if 'timeout' not in kwargs and hasattr(fn, '__self__'):
                # If it's a requests call, add timeout
                pass
            return fn(*args, **kwargs)
        
        return wrapped
    
    def safe_execute(
        self,
        fn: Callable,
        fallback: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Executes fn safely. If it fails even after retries, fallback is used.
        
        Args:
            fn: Function to execute
            fallback: Optional fallback function (called with no args if fn fails)
            *args: Positional arguments for fn
            **kwargs: Keyword arguments for fn
        
        Returns:
            Result from fn, fallback(), or None
        """
        try:
            wrapped = self.with_retry(fn)
            result = wrapped(*args, **kwargs)
            self._log("info", f"{fn.__name__} succeeded.")
            return result
        
        except Exception as e:
            error_msg = (
                f"{fn.__name__} failed after retries: {str(e)} — "
                f"falling back to: {fallback.__name__ if fallback else 'None'}"
            )
            self._log("error", error_msg)
            self._log("debug", traceback.format_exc())
            
            if fallback:
                try:
                    return fallback()
                except Exception as fallback_error:
                    self._log("error", f"Fallback also failed: {str(fallback_error)}")
                    return None
            
            return None
    
    def execute(
        self,
        func: Callable,
        *args,
        fallback_value: Any = None,
        fallback_func: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Alias for safe_execute (backward compatibility).
        
        Args:
            func: Function to execute
            *args: Positional arguments
            fallback_value: Value to return if execution fails
            fallback_func: Fallback function
            **kwargs: Keyword arguments
        
        Returns:
            Result from func, fallback_func(), or fallback_value
        """
        def _fallback():
            if fallback_func:
                return fallback_func(*args, **kwargs)
            return fallback_value
        
        result = self.safe_execute(func, fallback=_fallback if (fallback_func or fallback_value is not None) else None, *args, **kwargs)
        return result if result is not None else fallback_value
    
    def safe_request(
        self,
        method: str,
        url: str,
        fallback_value: Any = None,
        **request_kwargs
    ) -> Optional[requests.Response]:
        """
        Make a safe HTTP request with retry and timeout.
        
        Args:
            method: HTTP method (get, post, etc.)
            url: Request URL
            fallback_value: Value to return if request fails
            **request_kwargs: Additional arguments for requests
        
        Returns:
            Response object or fallback_value
        """
        # Set default timeout
        if 'timeout' not in request_kwargs:
            request_kwargs['timeout'] = self.config.timeout_secs
        
        def _make_request():
            return requests.request(method, url, **request_kwargs)
        
        def _fallback():
            return fallback_value
        
        return self.safe_execute(_make_request, fallback=_fallback if fallback_value is not None else None)


# Global safe executor instance
_default_executor = SafeExecutor()


def safe_fetch(
    func: Callable,
    *args,
    fallback_value: Any = None,
    fallback_func: Optional[Callable] = None,
    executor: Optional[SafeExecutor] = None,
    **kwargs
) -> Any:
    """
    Convenience function for safe fetching with retry logic.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        fallback_value: Value to return on failure
        fallback_func: Fallback function
        executor: SafeExecutor instance (uses default if None)
        **kwargs: Keyword arguments
    
    Returns:
        Result from func, fallback_func, or fallback_value
    """
    exec_instance = executor or _default_executor
    return exec_instance.execute(
        func,
        *args,
        fallback_value=fallback_value,
        fallback_func=fallback_func,
        **kwargs
    )


def safe_request(
    method: str,
    url: str,
    fallback_value: Any = None,
    executor: Optional[SafeExecutor] = None,
    **request_kwargs
) -> Optional[requests.Response]:
    """
    Convenience function for safe HTTP requests.
    
    Args:
        method: HTTP method
        url: Request URL
        fallback_value: Value to return on failure
        executor: SafeExecutor instance
        **request_kwargs: Request arguments
    
    Returns:
        Response object or fallback_value
    """
    exec_instance = executor or _default_executor
    return exec_instance.safe_request(
        method,
        url,
        fallback_value=fallback_value,
        **request_kwargs
    )

