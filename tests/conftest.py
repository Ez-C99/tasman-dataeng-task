"""Pytest configuration for logging.

Sets up a dedicated logger for smoke (and potentially other) tests so that
INFO-level summary lines are always emitted without enabling noisy INFO logs
from third-party libraries.
"""

from __future__ import annotations

import logging


def pytest_configure(config):
    # Create an isolated logger for our DQ smoke summaries.
    logger = logging.getLogger("dq.smoke")
    logger.setLevel(logging.INFO)
    if not logger.handlers:  # idempotent
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        # Prevent double logging via root.
        logger.propagate = False

    # Optional: if you want automatic CLI logging without -s or explicit flags, uncomment:
    # config.option.log_cli = True
    # config.option.log_cli_level = "INFO"
