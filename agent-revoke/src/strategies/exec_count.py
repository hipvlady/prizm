from __future__ import annotations
from typing import TYPE_CHECKING

from .base import RevocationStrategy
from src.core.mesi import MESIState, TransientState

if TYPE_CHECKING:
    from agent.runtime import AgentRuntime
    from core.types import Capability, RevocationEvent


class ExecCountStrategy(RevocationStrategy):
    """
    Release Consistency-directed Coherence (RCC). Agent self-invalidates after a
    maximum number of operations. It is clock-independent.
    """
    def __init__(self, max_operations: int = 50):
        self.max_operations = max_operations

    def on_grant(self, agent: AgentRuntime, capability: Capability) -> Capability:
        return capability

    def on_delegate(self, agent: AgentRuntime, parent_cap: Capability, child_cap: Capability) -> tuple[Capability, Capability]:
        new_parent_data = parent_cap.to_dict()
        new_parent_data["state"] = MESIState.MODIFIED
        new_parent_cap = Capability(**new_parent_data)
        return new_parent_cap, child_cap

    def on_revoke(self, agent: AgentRuntime, event: RevocationEvent) -> Capability:
        """Authority can still send an out-of-band revocation."""
        cap = agent.state.capabilities[event.capability_id]
        new_cap_data = cap.to_dict()
        new_cap_data["state"] = MESIState.INVALID
        return Capability(**new_cap_data)

    def on_action(self, agent: AgentRuntime, capability: Capability) -> Capability:
        """
        This is the "release" part of the RCC cycle.
        If the operation count is exhausted, the capability is invalidated and
        must be re-acquired from the authority.
        """
        # The check is `operations_used < max_operations`.
        # When `operations_used == max_operations`, it's exhausted.
        if capability.max_operations is not None and capability.operations_used >= capability.max_operations:
            new_cap_data = capability.to_dict()
            new_cap_data["state"] = MESIState.INVALID
            # Trigger the 'acquire' cycle by entering a transient state.
            new_cap_data["transient_state"] = TransientState.ISG # Invalid-to-Shared-waiting-Grant
            new_cap_data["transient_entered_tick"] = agent.clock.now()
            return Capability(**new_cap_data)

        # Increment operations used *after* a successful action in the agent runtime
        return capability

    def on_tick(self, agent: AgentRuntime, tick: int):
        pass # Exec-count strategy is not time-dependent