from __future__ import annotations
from typing import TYPE_CHECKING

from .base import RevocationStrategy
from src.core.mesi import MESIState

if TYPE_CHECKING:
    from agent.runtime import AgentRuntime
    from core.types import Capability, RevocationEvent

class EagerInvalidationStrategy(RevocationStrategy):
    """
    Consistency-Agnostic (SWMR-enforcing). Revocation blocks until all agents ACK.
    This is the simplest, most consistent strategy. When a revocation event is received,
    the capability is immediately marked as INVALID.
    """

    def on_grant(self, agent: AgentRuntime, capability: Capability) -> Capability:
        return capability

    def on_delegate(self, agent: AgentRuntime, parent_cap: Capability, child_cap: Capability) -> tuple[Capability, Capability]:
        """On delegation, the parent moves to MODIFIED state."""
        new_parent_data = parent_cap.to_dict()
        new_parent_data["state"] = MESIState.MODIFIED
        new_parent_cap = Capability(**new_parent_data)
        return new_parent_cap, child_cap

    def on_revoke(self, agent: AgentRuntime, event: RevocationEvent) -> Capability:
        """On revocation, the capability becomes INVALID immediately."""
        cap = agent.state.capabilities[event.capability_id]
        new_cap_data = cap.to_dict()
        new_cap_data["state"] = MESIState.INVALID
        return Capability(**new_cap_data)

    def on_action(self, agent: AgentRuntime, capability: Capability) -> Capability:
        return capability

    def on_tick(self, agent: AgentRuntime, tick: int):
        pass  # Eager strategy is not time-dependent