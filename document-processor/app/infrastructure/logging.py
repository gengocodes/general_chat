"""Centralized logging configuration for Document-Processor."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with standard timestamped formatting."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
