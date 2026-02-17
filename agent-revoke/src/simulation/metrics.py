from dataclasses import dataclass, field
from typing import List
import statistics

from rich.table import Table

@dataclass
class SimulationMetrics:
    scenario: str
    strategy: str
    total_ticks: int
    revocation_latency_p50: float
    revocation_latency_p99: float
    unauthorized_actions_count: int
    convergence_time_ticks: int
    message_overhead: int
    operations_wasted_on_revalidation: int

    def summary_table(self) -> str:
        table = Table(title=f"Metrics for {self.scenario} with {self.strategy} strategy")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Ticks", str(self.total_ticks))
        table.add_row("P50 Revocation Latency", f"{self.revocation_latency_p50:.2f} ticks")
        table.add_row("P99 Revocation Latency", f"{self.revocation_latency_p99:.2f} ticks")
        table.add_row("Unauthorized Actions", str(self.unauthorized_actions_count))
        table.add_row("Convergence Time", f"{self.convergence_time_ticks} ticks")
        table.add_row("Message Overhead", str(self.message_overhead))
        table.add_row("Wasted Ops on Re-validation", str(self.operations_wasted_on_revalidation))
        
        from rich.console import Console
        console = Console()
        with console.capture() as capture:
            console.print(table)
        return capture.get()

class MetricsCollector:
    def __init__(self):
        self._latencies: List[float] = []
        self._unauthorized_actions = 0
        self._messages = 0
        self._wasted_ops = 0

    def record_revocation_latency(self, ticks: float) -> None:
        self._latencies.append(ticks)

    def record_unauthorized_action(self) -> None:
        self._unauthorized_actions += 1

    def record_message(self) -> None:
        self._messages += 1
        
    def record_wasted_ops(self, count: int) -> None:
        self._wasted_ops += count

    def finalize(self, scenario: str, strategy: str, total_ticks: int, convergence_time: int = 0) -> SimulationMetrics:
        p50 = statistics.median(self._latencies) if self._latencies else 0
        p99 = statistics.quantiles(self._latencies, n=100)[-1] if self._latencies and len(self._latencies) > 1 else 0
        
        return SimulationMetrics(
            scenario=scenario,
            strategy=strategy,
            total_ticks=total_ticks,
            revocation_latency_p50=p50,
            revocation_latency_p99=p99,
            unauthorized_actions_count=self._unauthorized_actions,
            convergence_time_ticks=convergence_time,
            message_overhead=self._messages,
            operations_wasted_on_revalidation=self._wasted_ops
        )
