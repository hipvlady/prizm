from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, List
from uuid import UUID
from collections import defaultdict
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.core.types import RevocationEvent
    from src.agent.runtime import AgentRuntime

@dataclass
class MonitoredEvent:
    event: "RevocationEvent"
    agents_to_notify: Set[UUID]

class ConsistencyMonitor:
    """
    Monitors the state of capabilities across all agents to measure
    consistency metrics like revocation convergence time and staleness.
    (Spec §2.5)
    """

    def __init__(self):
        # Tracks which agents need to ACK a given revocation event
        self._pending_events: Dict[UUID, MonitoredEvent] = {}
        # Stores the latency for each converged event
        self._convergence_latencies: List[int] = []

    def record_revocation_broadcast(self, event: "RevocationEvent", agents_to_notify: Set[UUID]) -> None:
        """
        Called when the authority broadcasts a revocation. Records which agents
        are expected to receive and acknowledge the event.
        """
        self._pending_events[event.id] = MonitoredEvent(event, agents_to_notify)

    def record_agent_ack(self, agent_id: UUID, event_id: UUID, current_tick: int) -> None:
        """
        Called when an agent acknowledges receipt of a revocation event.
        """
        if event_id in self._pending_events:
            monitored = self._pending_events[event_id]
            monitored.agents_to_notify.discard(agent_id)
            if not monitored.agents_to_notify:
                # This was the last agent, the event has converged
                latency = current_tick - monitored.event.issued_tick
                self._convergence_latencies.append(latency)
                del self._pending_events[event_id]

    def get_convergence_latencies(self) -> List[int]:
        """Returns the list of convergence latencies for all fully propagated events."""
        return self._convergence_latencies

    def check_staleness(self, agents: Dict[UUID, "AgentRuntime"], tick: int) -> None:
        """
        Iterates through all agents to find capabilities that are known to be
        revoked by the authority but are still considered valid by the agent.
        This would require access to the authority's view of the world (registry).
        """
        # This is a complex method that requires comparing each agent's cache
        # against the central authority's registry.
        # Placeholder for now.
        pass

    def get_pending_ack_count(self, event_id: UUID) -> int:
        """
        Returns the number of agents that still need to acknowledge an event.
        """
        if event_id in self._pending_events:
            return len(self._pending_events[event_id].agents_to_notify)
        return 0
