"""Logging configuration."""

import logging
import sys
from backend.app.core.config import settings


def configure_logging() -> None:
    """Configure structured console logging according to environment settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
