"""
Centralized logging configuration for ProductivityGo.

REFACTOR-007: Standardized logging across the entire project.
This module provides a unified logging system that replaces print() statements
with proper logging that supports:
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured output format
- Request/user tracking for production debugging
- Environment-aware configuration

Usage:
    from utils.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Battle processing started")
    logger.error(f"Failed to process battle: {error}")
"""
import logging
import sys
import os
from contextvars import ContextVar
from typing import Optional

# -----------------------------------------------------------------------------
# Context Variables for Request Tracking
# These can be set by middleware to track requests across async operations
# -----------------------------------------------------------------------------
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Default log level - can be overridden by LOG_LEVEL environment variable
DEFAULT_LOG_LEVEL = logging.INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Map string log level names to logging constants
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# -----------------------------------------------------------------------------
# Format Strings
# -----------------------------------------------------------------------------
# Detailed format with context (used in development)
DETAILED_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"

# Simple format for production (reduces log size)
SIMPLE_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"

# JSON format for log aggregation systems
JSON_FORMAT = '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","line":%(lineno)d,"message":"%(message)s"}'


# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
def _get_log_level() -> int:
    """Get the configured log level as integer."""
    level_name = LOG_LEVEL
    level = LOG_LEVEL_MAP.get(level_name, DEFAULT_LOG_LEVEL)
    return level


def _get_format_string() -> str:
    """Get the appropriate format string based on environment."""
    # Check for JSON format requirement
    if os.getenv("LOG_FORMAT", "").lower() == "json":
        return JSON_FORMAT
    return DETAILED_FORMAT


def _configure_logging() -> None:
    """
    Configure the root logger with appropriate handlers and formatters.

    This function is called once at module import time.
    It sets up:
    - Console handler with appropriate format
    - Log level based on LOG_LEVEL environment variable
    - No file logging (handled by infrastructure in production)
    """
    root_logger = logging.getLogger()
    log_level = _get_log_level()
    format_string = _get_format_string()

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set root logger level
    root_logger.setLevel(log_level)


# Configure logging on module import
_configure_logging()


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.

    This function replaces print() statements with proper logging throughout
    the codebase. All loggers inherit configuration from the root logger.

    Args:
        name: The name of the module (typically __name__)

    Returns:
        A configured logger instance

    Examples:
        >>> from utils.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Battle processing started")
        >>> logger.debug(f"Processing round {round_num} for battle {battle_id}")
        >>> logger.error(f"Failed to complete battle: {error}")

    Log Level Guidelines:
        - DEBUG: Detailed diagnostic information (development only)
        - INFO: General informational messages (normal operation)
        - WARNING: Something unexpected but recoverable
        - ERROR: Error occurred but application can continue
        - CRITICAL: Serious error, application may not recover
    """
    return logging.getLogger(name)


def get_logger_with_context(name: str, request_id: Optional[str] = None, user_id: Optional[str] = None) -> logging.LoggerAdapter:
    """
    Get a logger with additional context for request tracking.

    This is useful for tracking specific requests through the system.
    The context is automatically included in log messages.

    Args:
        name: The name of the module (typically __name__)
        request_id: Optional request ID for tracing
        user_id: Optional user ID for auditing

    Returns:
        A LoggerAdapter that adds context to all log messages

    Examples:
        >>> logger = get_logger_with_context(__name__, request_id="req-123", user_id="user-456")
        >>> logger.info("User started battle")
        # Output: [timestamp] [INFO] [req-123] [user-456] User started battle
    """
    logger = logging.getLogger(name)

    # Create adapter that adds context to log records
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add context to the message
            parts = []
            if request_id:
                parts.append(f"[req-{request_id[:8]}]")  # Truncated for readability
            if user_id:
                parts.append(f"[user-{user_id[:8]}]")
            if parts:
                prefix = " ".join(parts)
                return f"{prefix} {msg}", kwargs
            return msg, kwargs

    return ContextAdapter(logger, extra={})


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """
    Set the request context variables for the current async context.

    This is typically called by middleware when a request starts.

    Args:
        request_id: Unique identifier for this request
        user_id: Optional user ID if user is authenticated
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    else:
        user_id_var.set(None)


def clear_request_context() -> None:
    """Clear the request context variables (end of request)."""
    request_id_var.set(None)
    user_id_var.set(None)


def get_request_context() -> dict:
    """
    Get the current request context as a dictionary.

    Returns:
        Dictionary with 'request_id' and 'user_id' keys
    """
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
    }
