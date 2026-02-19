# Copyright (c) 2026 Prizm contributors.
"""Local agent capability cache operations."""

from __future__ import annotations

from typing import Dict, Optional
from uuid import UUID

from src.core.mesi import MESIState, TransientState
from src.core.types import AgentState, Capability
from src.simulation.metrics import MetricsCollector


class AgentCache:
    """Manage local cache state for one agent."""

    def __init__(
        self,
        agent_id: UUID,
        transient_timeout_ticks: int,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """Initialise cache.

        Parameters
        ----------
        agent_id : UUID
            Agent identifier.
        transient_timeout_ticks : int
            Fail-safe timeout for transient states.
        metrics_collector : MetricsCollector, optional
            Metrics sink for timeout counters.
        """
        self.state = AgentState(agent_id=agent_id)
        self.transient_timeout_ticks = transient_timeout_ticks
        self.metrics_collector = metrics_collector

    @property
    def capabilities(self) -> Dict[UUID, Capability]:
        """Return capability mapping."""
        return self.state.capabilities

    def get(self, capability_id: UUID) -> Optional[Capability]:
        """Fetch capability by identifier."""
        return self.state.capabilities.get(capability_id)

    def update(self, capability: Capability):
        """Insert or replace a capability record."""
        self.state.capabilities[capability.id] = capability

    def increment_ops(self, capability_id: UUID):
        """Increment operation counter for operation-bounded capability."""
        cap = self.get(capability_id)
        if cap and cap.max_operations is not None:
            new_cap_dict = cap.to_dict()
            new_cap_dict["operations_used"] += 1
            self.update(Capability(**new_cap_dict))

    def find_by_resource(self, resource: str) -> Optional[Capability]:
        """Find first non-invalid capability for a resource."""
        for cap in self.state.capabilities.values():
            if cap.resource == resource and cap.state != MESIState.INVALID:
                return cap
        return None

    def find_any_by_resource(self, resource: str) -> Optional[Capability]:
        """Find first capability for a resource regardless of state."""
        for cap in self.state.capabilities.values():
            if cap.resource == resource:
                return cap
        return None

    def invalidate(self, capability_id: UUID) -> bool:
        """Force a capability into ``INVALID`` stable state.

        Parameters
        ----------
        capability_id : UUID
            Capability identifier.

        Returns
        -------
        bool
            ``True`` when a non-invalid capability was transitioned to
            ``INVALID``.
        """
        cap = self.get(capability_id)
        if cap and cap.state != MESIState.INVALID:
            new_cap_data = cap.to_dict()
            new_cap_data["state"] = MESIState.INVALID
            new_cap_data["transient_state"] = None
            new_cap_data["transient_entered_tick"] = None
            self.update(Capability(**new_cap_data))
            return True
        return False

    def enter_transient_state(self, capability_id: UUID, transient_state: TransientState, tick: int):
        """Set capability into transient state with entry tick."""
        cap = self.get(capability_id)
        if cap:
            new_cap_data = cap.to_dict()
            new_cap_data["transient_state"] = transient_state
            new_cap_data["transient_entered_tick"] = tick
            self.update(Capability(**new_cap_data))

    def clear_transient_state(self, capability_id: UUID):
        """Clear transient markers after successful resolution."""
        cap = self.get(capability_id)
        if cap:
            new_cap_data = cap.to_dict()
            new_cap_data["transient_state"] = None
            new_cap_data["transient_entered_tick"] = None
            self.update(Capability(**new_cap_data))

    def check_transient_timeouts(self, tick: int) -> list[UUID]:
        """Apply ADR-005 fail-safe timeout for transient states.

        Parameters
        ----------
        tick : int
            Current logical tick.

        Returns
        -------
        list[UUID]
            Capability identifiers forced to ``INVALID`` by timeout.
        """
        timed_out: list[UUID] = []
        for cap_id, cap in list(self.state.capabilities.items()):
            if cap.transient_state and cap.transient_entered_tick is not None:
                if (tick - cap.transient_entered_tick) > self.transient_timeout_ticks:
                    if self.invalidate(cap_id):
                        timed_out.append(cap_id)
                    if self.metrics_collector is not None:
                        self.metrics_collector.record_transient_timeout()
        return timed_out
