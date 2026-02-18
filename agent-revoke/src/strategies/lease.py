from __future__ import annotations
from typing import TYPE_CHECKING

from .base import RevocationStrategy
from src.core.mesi import MESIState
from src.core.types import RevocationReason

if TYPE_CHECKING:
    from agent.runtime import AgentRuntime
    from core.types import Capability, RevocationEvent


class LeaseBasedStrategy(RevocationStrategy):
    """
    Temporal Coherence. Agent self-invalidates when its time-based lease expires.
    Each capability is granted with a TTL (`expires_tick`). The agent is responsible
    for honoring this limit and self-invalidating its cache.
    """
    def __init__(self, default_ttl_ticks: int = 500):
        self.default_ttl_ticks = default_ttl_ticks

    def on_grant(self, agent: AgentRuntime, capability: Capability) -> Capability:
        return capability

    def on_delegate(self, agent: AgentRuntime, parent_cap: Capability, child_cap: Capability) -> tuple[Capability, Capability]:
        new_parent_data = parent_cap.to_dict()
        new_parent_data["state"] = MESIState.MODIFIED
        new_parent_cap = Capability(**new_parent_data)
        return new_parent_cap, child_cap

    def on_revoke(self, agent: AgentRuntime, event: RevocationEvent) -> Capability:
        """Authority can still send an out-of-band revocation to cut a lease short."""
        cap = agent.state.capabilities[event.capability_id]
        new_cap_data = cap.to_dict()
        new_cap_data["state"] = MESIState.INVALID
        return Capability(**new_cap_data)

    def on_action(self, agent: AgentRuntime, capability: Capability) -> Capability:
        """Check for expiration before use."""
        if capability.expires_tick is not None and agent.clock.now() >= capability.expires_tick:
            new_cap_data = capability.to_dict()
            new_cap_data["state"] = MESIState.INVALID
            return Capability(**new_cap_data)
        return capability

    def on_tick(self, agent: AgentRuntime, tick: int):
        """Proactively check for and invalidate expired leases."""
        for cap_id, cap in list(agent.state.capabilities.items()):
            if cap.state != MESIState.INVALID and cap.expires_tick is not None and tick >= cap.expires_tick:
                agent.invalidate_capability(cap_id, RevocationReason.EXPIRED, tick)