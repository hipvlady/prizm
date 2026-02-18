from dataclasses import dataclass, field
from typing import List, Dict
import statistics
from collections import defaultdict

from rich.table import Table

from src.core.types import ActionRecord

@dataclass
class SimulationMetrics:
    scenario: str
    strategy: str
    total_ticks: int
    total_actions: int
    unauthorized_actions_count: int
    unauthorized_actions_by_depth: Dict[int, int]

    def summary_table(self) -> str:
        table = Table(title=f"Metrics for {self.scenario} with {self.strategy} strategy")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Ticks", str(self.total_ticks))
        table.add_row("Total Actions", str(self.total_actions))
        table.add_row("Unauthorized Actions", str(self.unauthorized_actions_count))

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

    def record_action(self, record: ActionRecord):
        self._actions.append(record)

    def record_unauthorized_action(self, record: ActionRecord) -> None:
        self._unauthorized_actions.append(record)
        self._unauthorized_actions_by_depth[record.delegation_depth] += 1

    def finalize(self, scenario: str, strategy: str, total_ticks: int) -> SimulationMetrics:
        return SimulationMetrics(
            scenario=scenario,
            strategy=strategy,
            total_ticks=total_ticks,
            total_actions=len(self._actions),
            unauthorized_actions_count=len(self._unauthorized_actions),
            unauthorized_actions_by_depth=dict(self._unauthorized_actions_by_depth)
        )

