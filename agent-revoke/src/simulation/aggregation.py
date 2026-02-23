# Copyright (c) 2026 Prizm contributors.
"""Statistical aggregation of multi-run simulation metrics."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from src.simulation.metrics import SimulationMetrics


@dataclass
class AggregatedMetrics:
    """Mean +/- sigma across multiple runs for a single strategy-scenario pair."""

    scenario: str
    strategy: str
    num_runs: int
    seed_range: str

    unauthorized_ops_mean: float
    unauthorized_ops_std: float
    staleness_max_mean: float
    staleness_max_std: float
    latency_p50_mean: float
    latency_p50_std: float
    latency_p99_mean: float
    latency_p99_std: float
    messages_mean: float
    messages_std: float
    revalidation_mean: float
    revalidation_std: float
    convergence_mean: float
    convergence_std: float
    wall_time_mean: float
    wall_time_std: float

    unauthorized_by_depth_mean: dict[int, float] = field(default_factory=dict)
    unauthorized_by_depth_std: dict[int, float] = field(default_factory=dict)
    total_bound_violations: int = 0

    @classmethod
    def from_runs(
        cls,
        runs: list[SimulationMetrics],
        seed_start: int = 0,
    ) -> AggregatedMetrics:
        """Aggregate N SimulationMetrics into mean +/- sigma.

        Uses population std dev (pstdev) since the N runs represent
        the full experimental population, not a sample.
        """
        if not runs:
            raise ValueError("Cannot aggregate zero runs")

        n = len(runs)
        scenario = runs[0].scenario
        strategy = runs[0].strategy

        def _mean(vals: list[float]) -> float:
            return statistics.mean(vals)

        def _std(vals: list[float]) -> float:
            return statistics.pstdev(vals) if len(vals) > 1 else 0.0

        unauth = [float(r.unauthorized_actions_count) for r in runs]
        stale = [float(r.staleness_window_max) for r in runs]
        p50 = [r.revocation_latency_p50 for r in runs]
        p99 = [r.revocation_latency_p99 for r in runs]
        msgs = [float(r.message_overhead) for r in runs]
        reval = [float(r.revalidation_count) for r in runs]
        conv = [r.convergence_time for r in runs]
        wall = [r.wall_time_seconds for r in runs]

        # Per-depth aggregation
        all_depths: set[int] = set()
        for r in runs:
            all_depths.update(r.unauthorized_actions_by_depth.keys())

        depth_mean: dict[int, float] = {}
        depth_std: dict[int, float] = {}
        for d in sorted(all_depths):
            vals = [float(r.unauthorized_actions_by_depth.get(d, 0)) for r in runs]
            depth_mean[d] = _mean(vals)
            depth_std[d] = _std(vals)

        total_bv = sum(
            sum(r.bound_violations_by_depth.values()) for r in runs
        )

        return cls(
            scenario=scenario,
            strategy=strategy,
            num_runs=n,
            seed_range=f"{seed_start}-{seed_start + n - 1}",
            unauthorized_ops_mean=_mean(unauth),
            unauthorized_ops_std=_std(unauth),
            staleness_max_mean=_mean(stale),
            staleness_max_std=_std(stale),
            latency_p50_mean=_mean(p50),
            latency_p50_std=_std(p50),
            latency_p99_mean=_mean(p99),
            latency_p99_std=_std(p99),
            messages_mean=_mean(msgs),
            messages_std=_std(msgs),
            revalidation_mean=_mean(reval),
            revalidation_std=_std(reval),
            convergence_mean=_mean(conv),
            convergence_std=_std(conv),
            wall_time_mean=_mean(wall),
            wall_time_std=_std(wall),
            unauthorized_by_depth_mean=depth_mean,
            unauthorized_by_depth_std=depth_std,
            total_bound_violations=total_bv,
        )

    def format_metric(self, mean: float, std: float) -> str:
        """Format as 'mean +/- sigma' or just 'mean +/- 0' if sigma = 0."""
        if std == 0:
            return f"{mean:.1f} +/- 0"
        return f"{mean:.1f} +/- {std:.1f}"
