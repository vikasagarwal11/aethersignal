"""
Adaptive Chunking Engine (CHUNK 7.3.4)
Browser memory management and adaptive chunk size determination for Pyodide-based FAERS loading.
Prevents browser crashes and optimizes memory usage.
"""
from typing import Dict, Optional, Tuple
import sys


def get_available_memory_mb() -> float:
    """
    Estimate available browser memory in MB (Pyodide-compatible).
    
    Returns:
        Estimated available memory in megabytes
    """
    try:
        # In Pyodide/browser environment, we can try to get memory info
        # This is a fallback estimation since browser memory APIs are limited
        
        # Pyodide-specific: Check if we're in Pyodide
        try:
            import js  # Pyodide provides js module
            if hasattr(js, "performance") and hasattr(js.performance, "memory"):
                memory_info = js.performance.memory
                if memory_info:
                    # Convert bytes to MB
                    available = (memory_info.jsHeapSizeLimit - memory_info.usedJSHeapSize) / (1024 * 1024)
                    return max(100, available)  # Ensure minimum 100MB
        except:
            pass
        
        # Fallback: Conservative estimate
        # Most browsers allow ~2GB for a page, but we'll be conservative
        return 512.0  # Default to 512MB safe baseline
        
    except Exception:
        # Absolute fallback
        return 512.0


def determine_safe_chunksize(
    available_mb: Optional[float] = None,
    file_size_mb: Optional[float] = None,
    row_count_estimate: Optional[int] = None,
    num_parallel_workers: int = 1
) -> int:
    """
    Dynamically determine safe chunk size for FAERS loading based on available memory.
    
    Args:
        available_mb: Available memory in MB (if None, will estimate)
        file_size_mb: Size of file being loaded (optional, for optimization)
        row_count_estimate: Estimated number of rows (optional)
        num_parallel_workers: Number of parallel workers/processes (default: 1)
        
    Returns:
        Safe chunk size (number of rows per chunk)
    """
    if available_mb is None:
        available_mb = get_available_memory_mb()
    
    # Reserve 30% of memory for other operations
    usable_memory_mb = available_mb * 0.7
    
    # Account for parallel workers (each worker needs its own chunk)
    memory_per_worker_mb = usable_memory_mb / max(1, num_parallel_workers)
    
    # Estimate memory per row (conservative: ~1KB per row including overhead)
    bytes_per_row = 1024
    rows_per_mb = (1024 * 1024) / bytes_per_row  # ~1000 rows per MB
    
    # Calculate safe chunk size based on available memory
    if memory_per_worker_mb > 1500:
        base_chunksize = 50000  # Very safe for high memory
    elif memory_per_worker_mb > 800:
        base_chunksize = 30000
    elif memory_per_worker_mb > 400:
        base_chunksize = 15000
    elif memory_per_worker_mb > 200:
        base_chunksize = 8000
    else:
        base_chunksize = 4000  # Emergency mode - very conservative
    
    # Adjust based on file size if provided
    if file_size_mb:
        # Larger files should use smaller chunks
        if file_size_mb > 500:
            base_chunksize = int(base_chunksize * 0.5)
        elif file_size_mb > 200:
            base_chunksize = int(base_chunksize * 0.7)
    
    # Adjust based on row count estimate if provided
    if row_count_estimate:
        # For very large datasets, use smaller chunks
        if row_count_estimate > 1000000:  # >1M rows
            base_chunksize = int(base_chunksize * 0.5)
        elif row_count_estimate > 500000:  # >500K rows
            base_chunksize = int(base_chunksize * 0.7)
    
    # Ensure minimum and maximum bounds
    chunksize = max(1000, min(100000, base_chunksize))
    
    return int(chunksize)


def get_memory_safety_level(available_mb: Optional[float] = None) -> Dict[str, any]:
    """
    Get memory safety level and recommendations.
    
    Args:
        available_mb: Available memory in MB (if None, will estimate)
        
    Returns:
        Dictionary with safety level, recommendations, and limits
    """
    if available_mb is None:
        available_mb = get_available_memory_mb()
    
    if available_mb >= 1500:
        level = "excellent"
        recommendation = "High memory available. Can process large files safely."
        max_file_size_mb = 500
    elif available_mb >= 800:
        level = "good"
        recommendation = "Sufficient memory. Standard file processing should be safe."
        max_file_size_mb = 200
    elif available_mb >= 400:
        level = "moderate"
        recommendation = "Limited memory. Consider processing smaller files or using chunked loading."
        max_file_size_mb = 100
    elif available_mb >= 200:
        level = "low"
        recommendation = "Low memory detected. Use chunked loading and avoid large files."
        max_file_size_mb = 50
    else:
        level = "critical"
        recommendation = "Very low memory. Server-side processing recommended."
        max_file_size_mb = 20
    
    return {
        "level": level,
        "available_mb": round(available_mb, 1),
        "recommendation": recommendation,
        "max_file_size_mb": max_file_size_mb,
        "safe_chunksize": determine_safe_chunksize(available_mb),
        "warning": available_mb < 400
    }


def should_use_server_processing(
    file_size_mb: float,
    available_mb: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Determine if server-side processing should be used instead of local Pyodide.
    
    Args:
        file_size_mb: Size of file to process
        available_mb: Available memory in MB (if None, will estimate)
        
    Returns:
        Tuple of (should_use_server: bool, reason: str)
    """
    if available_mb is None:
        available_mb = get_available_memory_mb()
    
    safety = get_memory_safety_level(available_mb)
    max_file_size = safety["max_file_size_mb"]
    
    if file_size_mb > max_file_size:
        return True, f"File size ({file_size_mb:.1f}MB) exceeds safe local processing limit ({max_file_size}MB). Server processing recommended."
    
    if safety["level"] in ["low", "critical"]:
        return True, f"Low memory detected ({available_mb:.1f}MB). Server processing recommended for better reliability."
    
    return False, "Local processing is safe."


def optimize_chunking_strategy(
    file_size_mb: float,
    estimated_rows: Optional[int] = None,
    num_files: int = 1
) -> Dict[str, any]:
    """
    Optimize chunking strategy for multi-file FAERS loading.
    
    Args:
        file_size_mb: Total file size in MB
        estimated_rows: Estimated number of rows (optional)
        num_files: Number of files to process
        
    Returns:
        Dictionary with optimized chunking strategy
    """
    available_mb = get_available_memory_mb()
    safety = get_memory_safety_level(available_mb)
    
    # Calculate chunksize for each file
    file_size_per_file = file_size_mb / num_files if num_files > 0 else file_size_mb
    chunksize = determine_safe_chunksize(
        available_mb=available_mb,
        file_size_mb=file_size_per_file,
        row_count_estimate=estimated_rows,
        num_parallel_workers=num_files
    )
    
    # Estimate processing time (rough calculation)
    rows_per_second = 10000  # Conservative estimate
    estimated_chunks = (estimated_rows / chunksize) if estimated_rows else (file_size_mb / 2)  # Rough estimate
    estimated_time_seconds = estimated_chunks * 0.5  # ~0.5 seconds per chunk
    
    return {
        "chunksize": chunksize,
        "estimated_chunks": int(estimated_chunks),
        "estimated_time_seconds": round(estimated_time_seconds, 1),
        "estimated_time_minutes": round(estimated_time_seconds / 60, 1),
        "memory_safety": safety,
        "recommendation": "Local processing recommended" if not safety["warning"] else "Consider server processing for better reliability"
    }

