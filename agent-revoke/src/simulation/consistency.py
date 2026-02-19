# Copyright (c) 2026 Prizm contributors.
"""Consistency monitoring for revocation convergence and staleness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Set, Tuple
from uuid import UUID

from src.core.mesi import MESIState

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.authority.registry import CapabilityRegistry
    from src.core.types import RevocationEvent


@dataclass
class MonitoredEvent:
    """Internal structure for an event awaiting ACK convergence."""

    event: "RevocationEvent"
    agents_to_notify: Set[UUID]


class ConsistencyMonitor:
    """Track revocation convergence latencies and stale-authorisation windows."""

    def __init__(self):
        self._pending_events: Dict[UUID, MonitoredEvent] = {}
        self._completed_events: Dict[UUID, MonitoredEvent] = {}
        self._convergence_latencies: List[int] = []
        self._stale_started: Dict[Tuple[UUID, UUID], int] = {}
        self._staleness_window_max: int = 0

    def record_revocation_broadcast(self, event: "RevocationEvent", agents_to_notify: Set[UUID]) -> None:
        """Register an event broadcast and expected recipients."""
        for agent_id in agents_to_notify:
            event.propagated.setdefault(agent_id, None)
        self._pending_events[event.id] = MonitoredEvent(event, agents_to_notify)

    def record_agent_ack(self, agent_id: UUID, event_id: UUID, current_tick: int) -> None:
        """Register recipient ACK and close event once all ACKs are received."""
        if event_id in self._pending_events:
            monitored = self._pending_events[event_id]
            monitored.agents_to_notify.discard(agent_id)
            if not monitored.agents_to_notify:
                latency = current_tick - monitored.event.issued_tick
                self._convergence_latencies.append(latency)
                self._completed_events[event_id] = monitored
                del self._pending_events[event_id]

    def get_convergence_latencies(self) -> List[int]:
        """Return convergence latencies for completed events."""
        return self._convergence_latencies

    def check_staleness(
        self,
        agents: Dict[UUID, "AgentRuntime"],
        tick: int,
        registry: "CapabilityRegistry",
    ) -> None:
        """Update staleness windows by comparing local and canonical capability states.

        Parameters
        ----------
        agents : dict[UUID, AgentRuntime]
            Runtime agents keyed by identifier.
        tick : int
            Current logical tick.
        registry : CapabilityRegistry
            Authority-side canonical capability registry.
        """
        currently_stale: Set[Tuple[UUID, UUID]] = set()
        for agent_id, agent in agents.items():
            for cap_id, local_cap in agent.state.capabilities.items():
                authoritative = registry.get(cap_id)
                if authoritative is None:
                    continue

                is_stale = (
                    authoritative.state == MESIState.INVALID
                    and local_cap.state != MESIState.INVALID
                )
                key = (agent_id, cap_id)
                if is_stale:
                    currently_stale.add(key)
                    if key not in self._stale_started:
                        self._stale_started[key] = tick
                    self._staleness_window_max = max(
                        self._staleness_window_max,
                        tick - self._stale_started[key],
                    )

        for key in list(self._stale_started.keys()):
            if key not in currently_stale:
                stale_duration = tick - self._stale_started[key]
                self._staleness_window_max = max(self._staleness_window_max, stale_duration)
                del self._stale_started[key]

    def get_pending_ack_count(self, event_id: UUID) -> int:
        """Return count of recipients that still need to ACK an event."""
        if event_id in self._pending_events:
            return len(self._pending_events[event_id].agents_to_notify)
        return 0

    def get_propagation_map(self, event_id: UUID) -> Dict[UUID, int | None]:
        """Return propagation ACK timestamps for an event."""
        if event_id in self._pending_events:
            return dict(self._pending_events[event_id].event.propagated)
        if event_id in self._completed_events:
            return dict(self._completed_events[event_id].event.propagated)
        return {}

    def get_staleness_window_max(self) -> int:
        """Return maximum observed staleness window in ticks."""
        return self._staleness_window_max
