"""
Logger Setup - Centralized logging configuration
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs/"
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        log_dir: Log directory
    """
    # Create log directory
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine log file
    if not log_file:
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f"aethersignal_{timestamp}.log")
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Get log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels to suppress verbose output
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("postgrest").setLevel(logging.WARNING)
    logging.getLogger("gotrue").setLevel(logging.WARNING)
    logging.getLogger("realtime").setLevel(logging.WARNING)
    logging.getLogger("storage").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_logging_from_config():
    """Configure logging from system config."""
    try:
        from src.utils.config_loader import get_config_value
        log_level = get_config_value("log_level", "INFO")
        setup_logging(log_level=log_level)
    except Exception:
        # Fallback to default
        setup_logging()

