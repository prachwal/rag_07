"""
Logger utility module for structured logging.
Provides JSON-structured logging with configurable levels and file rotation.
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import structlog


def setup_logging(
    level: str = 'INFO',
    log_dir: Optional[Path] = None,
    json_format: bool = True,
    console_output: bool = True,
) -> None:
    """Setup structured logging configuration with file rotation."""

    # Ensure log directory exists
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='ISO'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if json_format
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup handlers
    handlers: list = []

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        handlers.append(console_handler)

    # File handler with daily rotation (keep 3 days)
    if log_dir:
        log_file = log_dir / "rag_07.log"
        file_handler = TimedRotatingFileHandler(
            log_file, when='midnight', interval=1, backupCount=3, encoding='utf-8'
        )
        file_handler.suffix = "%Y-%m-%d"
        handlers.append(file_handler)

    # Configure standard library logging
    logging.basicConfig(
        format='%(message)s',
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True,  # Override any existing configuration
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)

    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """Log an operation with structured data."""
        self.logger.info(
            'operation',
            operation=operation,
            class_name=self.__class__.__name__,
            **kwargs,
        )

    def log_error(
        self, error: Exception, operation: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log an error with structured data."""
        self.logger.error(
            'error_occurred',
            error_type=type(error).__name__,
            error_message=str(error),
            operation=operation,
            class_name=self.__class__.__name__,
            **kwargs,
        )


def configure_logging_from_env_and_config(
    config_manager=None,
    log_level_override: Optional[str] = None,
    log_dir_override: Optional[str] = None,
    console_output: bool = True,
) -> None:
    """Configure logging from environment, config and overrides."""
    import os

    # Priority: override > env > config > default
    log_level = (
        log_level_override
        or os.getenv('LOG_LEVEL')
        or (config_manager.config.log_level if config_manager else None)
        or 'INFO'
    )

    log_dir = log_dir_override or os.getenv('LOG_DIR') or 'logs'

    setup_logging(
        level=log_level,
        log_dir=Path(log_dir),
        json_format=True,
        console_output=console_output,
    )


# Initialize minimal logging on module import (will be reconfigured later)
setup_logging(level='WARNING', console_output=False)
