from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from .base import RevocationStrategy
from src.core.mesi import MESIState, TransientState

if TYPE_CHECKING:
    from agent.runtime import AgentRuntime
    from core.types import Capability, RevocationEvent


class LazyInvalidationStrategy(RevocationStrategy):
    """
    Consistency-Directed. Agent checks with authority on a defined interval ("check-on-use").
    The authority does not push revocations; the agent pulls validity information.
    """
    def __init__(self, check_interval_ticks: int = 100):
        self.check_interval_ticks = check_interval_ticks

    def on_grant(self, agent: AgentRuntime, capability: Capability) -> Capability:
        return capability

    def on_delegate(self, agent: AgentRuntime, parent_cap: Capability, child_cap: Capability) -> tuple[Capability, Capability]:
        new_parent_data = parent_cap.to_dict()
        new_parent_data["state"] = MESIState.MODIFIED
        new_parent_cap = Capability(**new_parent_data)
        return new_parent_cap, child_cap

    def on_revoke(self, agent: AgentRuntime, event: RevocationEvent) -> Optional[Capability]:
        # In Lazy mode, the agent doesn't process unsolicited revocations from the bus.
        # It will discover the invalidation during its next on_action or on_tick check.
        return None

    def on_action(self, agent: AgentRuntime, capability: Capability) -> Capability:
        """On action, check if the revalidation interval has passed."""
        if agent.clock.now() - agent.state.last_sync_tick > self.check_interval_ticks:
            # Time to revalidate. Enter a transient state.
            # The agent runtime will see this and issue a revalidation request.
            new_cap_data = capability.to_dict()
            new_cap_data["transient_state"] = TransientState.ISG # Invalid-to-Shared-waiting-Grant
            new_cap_data["transient_entered_tick"] = agent.clock.now()
            return Capability(**new_cap_data)
        return capability

    def on_tick(self, agent: AgentRuntime, tick: int):
        """Periodically re-validate capabilities based on the interval."""
        if tick - agent.state.last_sync_tick > self.check_interval_ticks:
            for cap in agent.state.capabilities.values():
                if cap.state == MESIState.INVALID:
                    continue
                # This is a simplified model. A real implementation would batch these.
                new_cap_data = cap.to_dict()
                new_cap_data["transient_state"] = TransientState.ISG
                new_cap_data["transient_entered_tick"] = agent.clock.now()
                agent.state.capabilities[cap.id] = Capability(**new_cap_data)
            agent.state.last_sync_tick = tick