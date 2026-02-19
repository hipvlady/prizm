# Copyright (c) 2026 Prizm contributors.
"""Terminal rendering helpers for simulation events."""

from __future__ import annotations

from rich.console import Console

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
