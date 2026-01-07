from __future__ import annotations

import logging
from typing import Final

import structlog

LOGGER_NAME: Final[str] = "ai_assistants"


def configure_logging() -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    """Create a bound logger instance for consistent structured logging."""
    return structlog.get_logger(LOGGER_NAME)


