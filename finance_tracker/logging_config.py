"""
Centralized logging configuration for the finance tracker application.

Provides consistent logging setup across all modules with support for
both console and file output.
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .constants import LOG_DATE_FORMAT, LOG_FORMAT, LOG_FILE


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If provided, logs are written to file.
    """
    # Create logger
    logger = logging.getLogger("finance_tracker")
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (use default if not provided)
    if log_file is None:
        log_file = LOG_FILE

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10_000_000,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module_name: Name of the module (usually __name__).

    Returns:
        Logger instance configured for the module.
    """
    return logging.getLogger(f"finance_tracker.{module_name}")
