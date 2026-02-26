# Copyright (c) 2026 Prizm contributors.
"""Terminal rendering helpers for simulation events."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


def _tick_prefix(tick: int | None) -> str:
    """Render a normalized tick prefix for terminal events."""
    if tick is None:
        return ""
    return f"[bold cyan][t={tick}][/bold cyan] "


def print_tick(tick: int, message: str) -> None:
    """Print tick-scoped message."""
    console.print(f"[bold cyan][t={tick:.3f}s][/bold cyan] {message}")


def print_grant(agent_id: str, resource: str, obo: str | None, tick: int | None = None) -> None:
    """Print grant event line."""
    prefix = _tick_prefix(tick)
    obo_value = obo if obo is not None else "-"
    console.print(f'{prefix}[green]GRANT[/green]  {agent_id} ← "{resource}" (OBO: {obo_value})')


def print_revoke(capability_id: str, reason: str, cascade: bool, tick: int | None = None) -> None:
    """Print revocation event line."""
    prefix = _tick_prefix(tick)
    console.print(
        f"{prefix}[bold red]⚡REVOKE[/bold red] capability={capability_id} reason={reason} cascade={cascade}"
    )


def print_ack(
    agent_id: str,
    mesi_transition: str,
    latency: int,
    tick: int | None = None,
) -> None:
    """Print revocation ACK line."""
    prefix = _tick_prefix(tick)
    console.print(f"{prefix}[green]✓ ACK[/green]   {agent_id} [MESI: {mesi_transition}] {latency}ms")


def print_deny(agent_id: str, resource: str, reason: str, tick: int | None = None) -> None:
    """Print denied action line."""
    prefix = _tick_prefix(tick)
    console.print(f"{prefix}[red]✗ DENY[/red]  {agent_id} attempted {resource} [{reason}]")


def print_action(agent_id: str, resource: str, tick: int | None = None) -> None:
    """Print allowed action line."""
    prefix = _tick_prefix(tick)
    console.print(f"{prefix}[dim]◌ACT[/dim]  {agent_id} {resource} [OK]")


def print_exhausted(
    agent_id: str,
    ops_used: int,
    max_ops: int,
    tick: int | None = None,
) -> None:
    """Print operation budget exhaustion line."""
    prefix = _tick_prefix(tick)
    console.print(f"{prefix}[cyan]⏹ EXHAUSTED[/cyan] {agent_id} ({ops_used}/{max_ops} ops)")


def print_deleg(from_agent: str, to_agent: str, scope: str, tick: int | None = None) -> None:
    """Print delegation line."""
    prefix = _tick_prefix(tick)
    console.print(f"{prefix}[yellow]DELEG[/yellow]  {from_agent} → {to_agent} (scope: {scope})")


def build_state_table(agents: dict[Any, Any]) -> Table:
    """Build per-agent state summary table."""
    table = Table(title="Agent MESI State")
    table.add_column("agent")
    table.add_column("states")
    table.add_column("trust")
    for agent_id, agent in sorted(agents.items(), key=lambda x: str(x[0])):
        states = sorted({cap.state.value for cap in agent.state.capabilities.values()})
        table.add_row(
            str(agent_id)[:8],
            ",".join(states) if states else "-",
            f"{agent.state.trust_score:.2f}",
        )
    return table


def build_summary_panel(metrics) -> Panel:
    """Build compact summary panel for key metrics."""
    body = (
        f"unauthorized={metrics.unauthorized_actions_count}\n"
        f"staleness_max={metrics.staleness_window_max}\n"
        f"cascade_ratio={metrics.cascade_completeness_ratio:.2f}\n"
        f"timeouts={metrics.transient_state_timeouts}"
    )
    return Panel(body, title="Simulation Summary")


class SimulationLiveView:
    """Minimal live terminal view for strategy, tick, and agent MESI states."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._live: Live | None = None

    def start(self) -> None:
        """Start live rendering session."""
        if not self.enabled:
            return
        self._live = Live(self._render_table(0, "init", {}), console=console, refresh_per_second=8)
        self._live.start()

    def stop(self) -> None:
        """Stop live rendering session."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def update(self, tick: int, strategy: str, agents: dict[Any, Any]) -> None:
        """Update table with latest simulation state."""
        if self._live is None:
            return
        state_map = {}
        for agent_id, agent in agents.items():
            states = sorted({cap.state.value for cap in agent.state.capabilities.values()})
            state_map[str(agent_id)[:8]] = ",".join(states) if states else "-"
        self._live.update(self._render_table(tick, strategy, state_map))

    @staticmethod
    def _render_table(tick: int, strategy: str, state_map: dict[str, str]) -> Table:
        table = Table(title="agent-revoke live")
        table.add_column("tick")
        table.add_column("strategy")
        table.add_column("agent")
        table.add_column("states")
        if not state_map:
            table.add_row(str(tick), strategy, "-", "-")
            return table
        first = True
        for agent, states in sorted(state_map.items()):
            if first:
                table.add_row(str(tick), strategy, agent, states)
                first = False
            else:
                table.add_row("", "", agent, states)
        return table


class LiveDashboard:
    """Context-manager wrapper around live updates."""

    def __init__(self) -> None:
        self._view = SimulationLiveView(enabled=True)

    def __enter__(self) -> "LiveDashboard":
        self._view.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self._view.stop()

    def update(
        self,
        tick: int,
        agents: dict[Any, Any],
        scenario_name: str,
        strategy_name: str,
    ) -> None:
        _ = scenario_name
        self._view.update(tick, strategy_name, agents)
