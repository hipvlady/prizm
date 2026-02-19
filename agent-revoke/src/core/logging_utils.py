# Copyright (c) 2026 Prizm contributors.
"""Shared structured logging configuration for simulation output."""

from __future__ import annotations

import logging
from typing import Optional

from rich.logging import RichHandler


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide structured logging with Rich rendering.

    Parameters
    ----------
    level : int, optional
        Root log level to apply, by default ``logging.INFO``.
    """
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = RichHandler(rich_tracebacks=True, show_time=True, show_path=False)
    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Return a logger optionally configured with a specific level.

    Parameters
    ----------
    name : str
        Logger name.
    level : int, optional
        Logger level override.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
