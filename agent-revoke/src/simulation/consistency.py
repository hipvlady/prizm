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
        self._cascade_completion_latencies: List[int] = []
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

    def mark_capability_invalidated(self, event_id: UUID, capability_id: UUID, current_tick: int) -> None:
        """Record capability-level invalidation progress for cascade certificate."""
        if event_id in self._pending_events:
            event = self._pending_events[event_id].event
        elif event_id in self._completed_events:
            event = self._completed_events[event_id].event
        else:
            return

        if capability_id in event.expected_capabilities:
            event.invalidated_capabilities.add(capability_id)
            if (
                event.cascade_completion_tick is None
                and event.expected_capabilities
                and event.invalidated_capabilities == event.expected_capabilities
            ):
                # RevocationEvent is frozen; use object.__setattr__ for the
                # completion tick metadata update.
                object.__setattr__(event, "cascade_completion_tick", current_tick)
                self._cascade_completion_latencies.append(current_tick - event.issued_tick)

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

    def get_expected_capabilities(self, event_id: UUID) -> Set[UUID]:
        """Return expected capability set for cascade completion certificate."""
        if event_id in self._pending_events:
            return set(self._pending_events[event_id].event.expected_capabilities)
        if event_id in self._completed_events:
            return set(self._completed_events[event_id].event.expected_capabilities)
        return set()

    def get_invalidated_capabilities(self, event_id: UUID) -> Set[UUID]:
        """Return invalidated capability set for cascade completion certificate."""
        if event_id in self._pending_events:
            return set(self._pending_events[event_id].event.invalidated_capabilities)
        if event_id in self._completed_events:
            return set(self._completed_events[event_id].event.invalidated_capabilities)
        return set()

    def get_cascade_completeness_ratio(self, event_id: UUID) -> float:
        """Return invalidated/expected ratio for a cascade event."""
        expected = self.get_expected_capabilities(event_id)
        if not expected:
            return 0.0
        invalidated = self.get_invalidated_capabilities(event_id)
        return len(invalidated) / len(expected)

    def get_cascade_completion_tick(self, event_id: UUID) -> int | None:
        """Return cascade completion tick if already completed."""
        if event_id in self._pending_events:
            return self._pending_events[event_id].event.cascade_completion_tick
        if event_id in self._completed_events:
            return self._completed_events[event_id].event.cascade_completion_tick
        return None

    def get_cascade_completion_latencies(self) -> List[int]:
        """Return list of completion latencies from issued tick to full cascade completion."""
        return list(self._cascade_completion_latencies)

    def get_overall_cascade_completeness_ratio(self) -> float:
        """Return aggregate invalidated/expected ratio across all known events."""
        events = list(self._pending_events.values()) + list(self._completed_events.values())
        if not events:
            return 0.0
        expected = 0
        invalidated = 0
        for monitored in events:
            expected += len(monitored.event.expected_capabilities)
            invalidated += len(monitored.event.invalidated_capabilities)
        if expected == 0:
            return 0.0
        return invalidated / expected
