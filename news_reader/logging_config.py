#!/usr/bin/env python3
"""
Logging Configuration - Centralized logging setup for the News Reader application
"""

import logging
import os
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    """
    Setup centralized logging configuration for the entire application.
    All logs will be written to logs.txt in the project root directory.
    
    Args:
        log_level: The logging level (default: INFO)
    """
    # Get the project root directory (parent of news_reader package)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    log_file_path = project_root / 'logs.txt'
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=str(log_file_path),
        filemode='a',  # Append mode to keep historical logs
        force=True  # Override any existing configuration
    )
    
    # Also ensure the root logger doesn't propagate to console
    root_logger = logging.getLogger()
    # Remove any existing handlers that might output to console
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler.stream.name in ['<stdout>', '<stderr>']:
            root_logger.removeHandler(handler)
    
    return str(log_file_path)

def get_logger(name):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
