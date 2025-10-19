#!/usr/bin/env python3
"""
Error Handling Utilities - Centralized error handling patterns
"""

import asyncio
from typing import Any, Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')

def handle_operation_error(
    operation_name: str, 
    logger_instance, 
    default_return: Any = None,
    reraise: bool = False
) -> Callable:
    """
    Decorator for consistent error handling across the application
    
    Args:
        operation_name: Description of the operation for logging
        logger_instance: Logger instance to use for error logging
        default_return: Value to return on error (default: None)
        reraise: Whether to re-raise the exception after logging (default: False)
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger_instance.error(f"Failed to {operation_name}: {e}")
                    if reraise:
                        raise
                    return default_return
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger_instance.error(f"Failed to {operation_name}: {e}")
                    if reraise:
                        raise
                    return default_return
            return sync_wrapper
    return decorator

def log_and_return_on_error(
    logger_instance, 
    operation_name: str, 
    default_return: Any = None
) -> Any:
    """
    Context manager for error handling with consistent logging
    
    Args:
        logger_instance: Logger instance to use
        operation_name: Description of the operation
        default_return: Value to return on error
    
    Returns:
        Context manager
    """
    class ErrorHandler:
        def __init__(self, logger, op_name, default):
            self.logger = logger
            self.op_name = op_name
            self.default = default
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                self.logger.error(f"Failed to {self.op_name}: {exc_val}")
                return True  # Suppress the exception
            return False
    
    return ErrorHandler(logger_instance, operation_name, default_return)
