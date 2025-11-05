"""
Centralized logging configuration for the application.

Provides structured logging with AWS Lambda compatibility and local development support.
"""

import logging
import sys
import json
from typing import Any, Dict
from datetime import datetime
from pythonjsonlogger import jsonlogger
from .config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.

    Adds timestamp, environment, and service name to all log records.
    """

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['environment'] = settings.ENVIRONMENT
        log_record['service'] = settings.APP_NAME
        log_record['level'] = record.levelname


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        name: Logger name (defaults to root logger)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    handler = logging.StreamHandler(sys.stdout)

    # Use JSON logging in production, human-readable in development
    if settings.ENVIRONMENT == "production":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Create default logger
logger = setup_logger()


def log_execution_time(func):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time
        def my_function():
            pass
    """
    import functools
    import time

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{func.__name__} executed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{func.__name__} executed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


import asyncio
