from __future__ import annotations
from typing import Dict, Optional
from uuid import UUID

from src.core.types import AgentState, Capability
from src.core.mesi import MESIState, TransientState

class AgentCache:
    """
    Manages the agent's local cache of capabilities, which is its view of the world.
    This corresponds to a CPU's L1 cache in the MESI analogy.
    """
    def __init__(self, agent_id: UUID, transient_timeout_ticks: int):
        self.state = AgentState(agent_id=agent_id)
        self.transient_timeout_ticks = transient_timeout_ticks

    @property
    def capabilities(self) -> Dict[UUID, Capability]:
        return self.state.capabilities

    def get(self, capability_id: UUID) -> Optional[Capability]:
        return self.state.capabilities.get(capability_id)

    def update(self, capability: Capability):
        """Updates or adds a capability to the cache."""
        self.state.capabilities[capability.id] = capability

    def increment_ops(self, capability_id: UUID):
        """Increments the operations_used counter for a capability."""
        cap = self.get(capability_id)
        if cap and cap.max_operations is not None:
            new_cap_dict = cap.to_dict()
            new_cap_dict['operations_used'] += 1
            self.update(Capability(**new_cap_dict))

    def find_by_resource(self, resource: str) -> Optional[Capability]:
        """Finds the first valid capability for a given resource."""
        for cap in self.state.capabilities.values():
            if cap.resource == resource and cap.state != MESIState.INVALID:
                return cap
        return None

    def invalidate(self, capability_id: UUID):
        """Marks a capability as Invalid in the cache."""
        cap = self.get(capability_id)
        if cap and cap.state != MESIState.INVALID:
            new_cap_data = cap.to_dict()
            new_cap_data["state"] = MESIState.INVALID
            new_cap_data["transient_state"] = None
            new_cap_data["transient_entered_tick"] = None
            self.update(Capability(**new_cap_data))

    def enter_transient_state(self, capability_id: UUID, transient_state: TransientState, tick: int):
        """Enters a transient state."""
        cap = self.get(capability_id)
        if cap:
            new_cap_data = cap.to_dict()
            new_cap_data["transient_state"] = transient_state
            new_cap_data["transient_entered_tick"] = tick
            self.update(Capability(**new_cap_data))
    
    def check_transient_timeouts(self, tick: int):
        """
        ADR-005: Fail-Safe. Iterates through all capabilities and invalidates any
        that have been in a transient state for too long.
        """
        for cap_id, cap in list(self.state.capabilities.items()):
            if cap.transient_state and cap.transient_entered_tick is not None:
                if (tick - cap.transient_entered_tick) > self.transient_timeout_ticks:
                    self.invalidate(cap_id)
