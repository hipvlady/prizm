# Copyright (c) 2026 Prizm contributors.
"""Per-depth operational bound helpers for unauthorized actions."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional


def calculate_depth_bound(
    strategy: str,
    depth: int,
    config: Dict[str, Any],
    *,
    remaining_ops_at_revoke: Optional[int] = None,
) -> int:
    """Return bound for unauthorized actions at delegation depth.

    Parameters
    ----------
    strategy : str
        Strategy name (`eager`, `lazy`, `lease`, `exec_count`).
    depth : int
        Delegation depth.
    config : dict
        Simulation configuration.
    remaining_ops_at_revoke : int, optional
        Remaining operation budget snapshot for exec-count.

    Returns
    -------
    int
        Maximum allowed unauthorised actions at the given depth.
    """
    simulation = config.get("simulation", {})
    strategies = config.get("strategies", {})
    if "actions_per_tick" in simulation:
        velocity = max(0, int(simulation.get("actions_per_tick", 0)))
    else:
        action_probability = float(simulation.get("action_probability", 0.0))
        # For probabilistic workloads, use worst-case one action per tick to avoid
        # under-estimating security bounds from expected-value rates.
        velocity = 1 if action_probability > 0 else 0
        anomaly_burst = int(config.get("scenario", {}).get("anomaly_burst_actions_per_tick", 0))
        velocity = max(velocity, anomaly_burst)
    network_latency = simulation.get("latency_ticks", 1)

    if strategy == "eager":
        return math.ceil(float(velocity) * (network_latency * (depth + 1)))
    if strategy == "lazy":
        check_interval = strategies.get("lazy", {}).get("check_interval_ticks", 100)
        return math.ceil(float(velocity) * (check_interval + network_latency * (depth + 1)))
    if strategy == "lease":
        ttl = strategies.get("lease", {}).get("default_ttl_ticks", 500)
        return math.ceil(float(velocity) * ttl)
    if strategy == "exec_count":
        if remaining_ops_at_revoke is not None:
            return max(0, remaining_ops_at_revoke)
        return int(strategies.get("exec_count", {}).get("max_operations", 50))

    return 0
