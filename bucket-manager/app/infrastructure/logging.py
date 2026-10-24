"""Application logging configuration for Bucket-Manager."""

import logging
import sys


def setup_logging() -> None:
    """Configure centralized logging format for the service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
