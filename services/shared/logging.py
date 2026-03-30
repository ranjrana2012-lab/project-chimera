"""
Shared logging configuration for Project Chimera services.
Provides structured logging with consistent formatting.
"""

import logging
import sys
import structlog
from typing import Any


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "json"
) -> None:
    """
    Configure structured logging for a service.

    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Log format ("json" or "text")
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, log_level.upper()),
        stream=sys.stdout,
    )

    # Configure structlog
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set service name in context
    structlog.contextvars.bind_contextvars(service_name=service_name)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


__all__ = ["configure_logging", "get_logger"]
