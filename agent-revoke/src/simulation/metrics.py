# Copyright (c) 2026 Prizm contributors.
"""Metrics data structures and collection utilities."""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from rich.table import Table

from src.core.types import ActionRecord
from src.simulation.consistency import ConsistencyMonitor
from src.strategies.base import ActionResult


@dataclass
class SimulationMetrics:
    """Immutable summary payload produced at the end of a simulation run."""

    scenario: str
    strategy: str
    total_ticks: int
    total_actions: int
    unauthorized_actions_count: int
    unauthorized_actions_by_depth: Dict[int, int]
    revocation_latency_p50: float = 0.0
    revocation_latency_p99: float = 0.0
    staleness_window_max: int = 0
    transient_state_duration_avg: float = 0.0
    transient_state_duration_max: int = 0
    transient_state_timeouts: int = 0
    unauthorized_actions_in_transient: int = 0
    unauthorized_actions_impact: int = 0
    convergence_time: float = 0.0
    message_overhead: int = 0
    revalidation_count: int = 0
    operations_wasted_on_revalidation: int = 0
    wall_time_seconds: float = 0.0
    avg_tick_seconds: float = 0.0
    p95_tick_seconds: float = 0.0
    cascade_completeness_ratio: float = 0.0
    cascade_completion_ticks: List[int] = field(default_factory=list)
    bound_violations_by_depth: Dict[int, int] = field(default_factory=dict)

    def summary_table(self) -> str:
        """Render a Rich table for terminal output."""
        table = Table(title=f"Metrics for {self.scenario} with {self.strategy} strategy")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Ticks", str(self.total_ticks))
        table.add_row("Total Actions", str(self.total_actions))
        table.add_row("Unauthorized Actions", str(self.unauthorized_actions_count))
        table.add_row("Max Staleness Window (ticks)", str(self.staleness_window_max))
        table.add_row("Avg. Convergence Time (ticks)", f"{self.convergence_time:.2f}")
        table.add_row("P50 Revocation Latency", f"{self.revocation_latency_p50:.2f}")
        table.add_row("P99 Revocation Latency", f"{self.revocation_latency_p99:.2f}")
        table.add_row("Transient State Timeouts", str(self.transient_state_timeouts))
        table.add_row("Message Overhead", str(self.message_overhead))
        table.add_row("Revalidations", str(self.revalidation_count))
        table.add_row("Wall Time (s)", f"{self.wall_time_seconds:.6f}")
        table.add_row("Avg Tick Time (s)", f"{self.avg_tick_seconds:.6f}")

        for depth, count in sorted(self.unauthorized_actions_by_depth.items()):
            table.add_row(f"  Unauthorized at Depth {depth}", str(count))

        from rich.console import Console

        console = Console()
        with console.capture() as capture:
            console.print(table)
        return capture.get()


class MetricsCollector:
    """Collect and aggregate simulation metrics."""

    def __init__(self):
        self._actions: List[ActionRecord] = []
        self._unauthorized_actions: List[ActionRecord] = []
        self._unauthorized_actions_by_depth: Dict[int, int] = defaultdict(int)
        self._revalidation_count: int = 0
        self._message_count: int = 0
        self._transient_state_timeouts: int = 0
        self._unauthorized_actions_in_transient: int = 0
        self._tick_durations: List[float] = []
        self._bound_violations_by_depth: Dict[int, int] = defaultdict(int)

    def record_action(self, record: ActionRecord):
        """Record an action event."""
        self._actions.append(record)

    def record_unauthorized_action(self, record: ActionRecord) -> None:
        """Record an action that was authorised locally but stale globally."""
        self._unauthorized_actions.append(record)
        self._unauthorized_actions_by_depth[record.delegation_depth] += 1
        if record.result == ActionResult.DENIED_TRANSIENT:
            self._unauthorized_actions_in_transient += 1

    def record_revalidation(self):
        """Increment revalidation counter."""
        self._revalidation_count += 1

    def record_message_broadcast(self, recipient_count: int):
        """Record broadcast overhead as recipient fanout count."""
        self._message_count += recipient_count

    def record_transient_timeout(self):
        """Record transient timeout fail-safe activation."""
        self._transient_state_timeouts += 1

    def record_tick_duration(self, seconds: float):
        """Record wall-clock duration of one simulation tick."""
        self._tick_durations.append(seconds)

    def record_bound_violation(self, depth: int) -> None:
        """Record a per-depth unauthorized bound violation."""
        self._bound_violations_by_depth[depth] += 1

    def finalize(
        self,
        scenario: str,
        strategy: str,
        total_ticks: int,
        monitor: ConsistencyMonitor,
        wall_time_seconds: float = 0.0,
    ) -> SimulationMetrics:
        """Create final metrics payload.

        Parameters
        ----------
        scenario : str
            Scenario label.
        strategy : str
            Strategy label.
        total_ticks : int
            Number of ticks executed.
        monitor : ConsistencyMonitor
            Monitor providing convergence and staleness data.
        wall_time_seconds : float, optional
            End-to-end runtime measured via ``time.perf_counter``.
        """
        latencies = monitor.get_convergence_latencies()
        p50 = 0.0
        p99 = 0.0
        avg_convergence = 0.0
        if latencies:
            if len(latencies) > 1:
                p50 = statistics.quantiles(latencies, n=100)[49]
                p99 = statistics.quantiles(latencies, n=100)[98]
            else:
                p50 = p99 = latencies[0]
            avg_convergence = statistics.mean(latencies)

        avg_tick_seconds = statistics.mean(self._tick_durations) if self._tick_durations else 0.0
        p95_tick_seconds = (
            statistics.quantiles(self._tick_durations, n=100)[94]
            if len(self._tick_durations) > 1
            else (self._tick_durations[0] if self._tick_durations else 0.0)
        )

        return SimulationMetrics(
            scenario=scenario,
            strategy=strategy,
            total_ticks=total_ticks,
            total_actions=len(self._actions),
            unauthorized_actions_count=len(self._unauthorized_actions),
            unauthorized_actions_by_depth=dict(self._unauthorized_actions_by_depth),
            revalidation_count=self._revalidation_count,
            message_overhead=self._message_count,
            revocation_latency_p50=p50,
            revocation_latency_p99=p99,
            convergence_time=avg_convergence,
            transient_state_timeouts=self._transient_state_timeouts,
            unauthorized_actions_in_transient=self._unauthorized_actions_in_transient,
            staleness_window_max=monitor.get_staleness_window_max(),
            wall_time_seconds=wall_time_seconds,
            avg_tick_seconds=avg_tick_seconds,
            p95_tick_seconds=p95_tick_seconds,
            cascade_completeness_ratio=monitor.get_overall_cascade_completeness_ratio(),
            cascade_completion_ticks=monitor.get_cascade_completion_latencies(),
            bound_violations_by_depth=dict(self._bound_violations_by_depth),
        )
