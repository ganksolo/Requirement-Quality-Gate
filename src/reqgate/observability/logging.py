"""Observability and logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO", name: str | None = None) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        name: Logger name, defaults to 'reqgate'

    Returns:
        Configured logger instance
    """
    logger_name = name or "reqgate"
    logger = logging.getLogger(logger_name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Console handler with structured format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Format: timestamp - name - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "reqgate") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
