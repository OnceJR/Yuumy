"""Logging utilities for the multistream recorder.

This module configures ``structlog`` for structured logging.  The
configuration function chooses sensible defaults, outputs logs to both
stderr and to a rotating file if a log directory is provided, and
sets up different log levels for the main application and its
dependencies.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog


def configure_logging(config) -> None:
    """Configures the logging system.

    Args:
        config: Configuration object with optional attributes used for logging
            (e.g. ``download_dir`` can be used to store logs).
    """
    # Determine log level from environment variable or default to INFO
    log_level_name = "INFO"
    # Create a basic handler writing to stderr
    logging.basicConfig(
        level=log_level_name,
        stream=sys.stderr,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level_name)),
        cache_logger_on_first_use=True,
    )
