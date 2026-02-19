# Copyright (c) 2026 Prizm contributors.
"""Scenario loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from src.core.logging_utils import get_logger

LOGGER = get_logger(__name__)


def load_scenario(scenario_path: str) -> Dict:
    """Load a YAML scenario file into a configuration dictionary.

    Parameters
    ----------
    scenario_path : str
        Path to the YAML scenario file.

    Returns
    -------
    dict
        Parsed scenario dictionary.
    """
    path = Path(scenario_path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    LOGGER.debug("event=scenario_loaded path=%s", path)
    return data
