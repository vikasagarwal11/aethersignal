"""
Safe executor with timeout for Streamlit applications.
Uses threading instead of multiprocessing for better compatibility.
"""
import threading
import time
from typing import Callable, Any, Tuple, Optional
from queue import Queue, Empty


def run_with_timeout(
    func: Callable,
    timeout_seconds: float,
    *args,
    **kwargs
) -> Tuple[str, Any]:
    """
    Runs a function with a timeout using threading.
    
    Args:
        func: Function to execute
        timeout_seconds: Maximum time to wait
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Tuple of (status, result) where status is:
        - "success": Function completed successfully
        - "timeout": Function exceeded timeout
        - "error": Function raised an exception
    """
    result_queue: Queue = Queue()
    error_queue: Queue = Queue()
    
    def _run_func():
        try:
            result = func(*args, **kwargs)
            result_queue.put(("success", result))
        except Exception as e:
            error_queue.put(("error", str(e)))
    
    # Start function in thread
    thread = threading.Thread(target=_run_func, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    # Check if thread is still alive (timeout occurred)
    if thread.is_alive():
        # Thread is still running - timeout
        return ("timeout", None)
    
    # Check for error first
    try:
        status, error = error_queue.get_nowait()
        return (status, error)
    except Empty:
        pass
    
    # Check for result
    try:
        status, result = result_queue.get_nowait()
        return (status, result)
    except Empty:
        # Thread finished but no result - assume error
        return ("error", "Function completed but returned no result")
