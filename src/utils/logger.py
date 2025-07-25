"""
Logger utility module for structured logging.
Provides JSON-structured logging with configurable levels.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog


def setup_logging(
    level: str = 'INFO', log_file: Optional[Path] = None, json_format: bool = True
) -> None:
    """Setup structured logging configuration."""
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

    # Configure standard library logging
    handlers: list = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        format='%(message)s', level=getattr(logging, level.upper()), handlers=handlers
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


# Initialize logging on module import
setup_logging()
