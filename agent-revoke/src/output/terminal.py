# Copyright (c) 2026 Prizm contributors.
"""Terminal rendering helpers for simulation events."""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()


def print_tick(tick: int, message: str):
    """Print tick-scoped message."""
    console.print(f"[bold cyan][t={tick:.3f}s][/bold cyan] {message}")


def print_grant(agent_id: str, resource: str, obo: str):
    """Print grant event line."""
    console.print(f'[green]GRANT[/green]  {agent_id} ← "{resource}" (OBO: {obo})')


def print_revoke(capability_id: str, reason: str, cascade: bool):
    """Print revocation event line."""
    console.print(
        f"[bold red]⚡REVOKE[/bold red] capability={capability_id} reason={reason} cascade={cascade}"
    )


def print_ack(agent_id: str, mesi_transition: str, latency: int):
    """Print revocation ACK line."""
    console.print(f"[green]✓ ACK[/green]   {agent_id} [MESI: {mesi_transition}] {latency}ms")


def print_deny(agent_id: str, resource: str, reason: str):
    """Print denied action line."""
    console.print(f"[red]✗ DENY[/red]  {agent_id} attempted {resource} [{reason}]")


def print_deleg(from_agent: str, to_agent: str, scope: str):
    """Print delegation line."""
    console.print(f"[yellow]DELEG[/yellow]  {from_agent} → {to_agent} (scope: {scope})")


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

    def update(self, tick: int, strategy: str, agents: dict) -> None:
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
