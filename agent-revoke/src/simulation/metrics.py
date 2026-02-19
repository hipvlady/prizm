from dataclasses import dataclass, field
from typing import List, Dict
import statistics
from collections import defaultdict

from rich.table import Table

from src.core.types import ActionRecord
from src.simulation.consistency import ConsistencyMonitor

@dataclass
class SimulationMetrics:
    scenario: str
    strategy: str
    total_ticks: int
    total_actions: int
    unauthorized_actions_count: int
    unauthorized_actions_by_depth: Dict[int, int]
    
    # Newly added metrics from spec §2.4
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

    def summary_table(self) -> str:
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

        for depth, count in sorted(self.unauthorized_actions_by_depth.items()):
            table.add_row(f"  Unauthorized at Depth {depth}", str(count))
        
        from rich.console import Console
        console = Console()
        with console.capture() as capture:
            console.print(table)
        return capture.get()

class MetricsCollector:
    def __init__(self):
        self._actions: List[ActionRecord] = []
        self._unauthorized_actions: List[ActionRecord] = []
        self._unauthorized_actions_by_depth: Dict[int, int] = defaultdict(int)
        self._revalidation_count: int = 0
        self._message_count: int = 0
        self._transient_state_timeouts: int = 0
        self._unauthorized_actions_in_transient: int = 0

    def record_action(self, record: ActionRecord):
        self._actions.append(record)

    def record_unauthorized_action(self, record: ActionRecord) -> None:
        self._unauthorized_actions.append(record)
        self._unauthorized_actions_by_depth[record.delegation_depth] += 1
        if record.result == ActionResult.DENIED_TRANSIENT:
            self._unauthorized_actions_in_transient += 1

    def record_revalidation(self):
        self._revalidation_count += 1
    
    def record_message_broadcast(self, recipient_count: int):
        self._message_count += recipient_count

    def record_transient_timeout(self):
        self._transient_state_timeouts += 1

    def finalize(self, scenario: str, strategy: str, total_ticks: int, monitor: ConsistencyMonitor) -> SimulationMetrics:
        
        latencies = monitor.get_convergence_latencies()
        p50 = 0.0
        p99 = 0.0
        avg_convergence = 0.0
        if latencies:
            # Ensure there are enough data points for quantiles
            if len(latencies) > 1:
                p50 = statistics.quantiles(latencies, n=100)[49]
                p99 = statistics.quantiles(latencies, n=100)[98]
            elif len(latencies) == 1:
                p50 = p99 = latencies[0]
            avg_convergence = statistics.mean(latencies)

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
        )

