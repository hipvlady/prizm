from __future__ import annotations
from typing import TYPE_CHECKING, List

from .base import RevocationStrategy, CoherenceClass, BoundType, ActionResult, StrategyMetrics
from src.core.mesi import MESIState
from src.core.types import Capability

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import RevocationEvent, ActionRecord


class LeaseBasedStrategy(RevocationStrategy):
    """
    Temporal Coherence. Agent self-invalidates when its time-based lease expires.
    Each capability is granted with a TTL (`expires_tick`). The agent is responsible
    for honoring this limit and self-invalidating its cache.
    """
    name: str = "lease"
    coherence_class: CoherenceClass = CoherenceClass.CONSISTENCY_DIRECTED
    bound_type: BoundType = BoundType.TIME

    def __init__(self, default_ttl_ticks: int = 500):
        self.default_ttl_ticks = default_ttl_ticks
        self._metrics = StrategyMetrics()

    def initiate_revocation(self, event: "RevocationEvent", agents: List["AgentRuntime"]) -> None:
        # Authority can still send an out-of-band revocation to cut a lease short.
        # The generic `on_revocation_received` in AgentRuntime will handle it.
        pass

    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """Check for expiration before use."""
        if capability.state == MESIState.INVALID:
            return ActionResult.DENIED

        if capability.expires_tick is not None and agent.clock.now() >= capability.expires_tick:
            agent.invalidate_capability(capability.id)
            return ActionResult.EXPIRED
            
        return ActionResult.ALLOWED

    def on_tick(self, agent: "AgentRuntime", tick: int) -> None:
        """Proactively check for and invalidate expired leases."""
        for cap_id, cap in list(agent.state.capabilities.items()):
            if cap.state != MESIState.INVALID and cap.expires_tick is not None and tick >= cap.expires_tick:
                agent.invalidate_capability(cap_id)

    def record_action(self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord") -> None:
        pass  # No specific recording logic for lease-based strategy

    def revalidate(self, agent: "AgentRuntime", capability: "Capability") -> Optional["Capability"]:
        """
        Requests a new capability from the authority after the old one has expired.
        """
        # The capability is already marked as INVALID by validate_action
        new_cap = agent.authority.grant_capability(
            agent_id=agent.agent_id,
            resource=capability.resource,
            scope=capability.scope,
            ttl=self.default_ttl_ticks,
        )
        if new_cap:
            agent.cache.update(new_cap)
        return new_cap

    def get_metrics(self) -> "StrategyMetrics":
        return self._metrics

    def get_theoretical_bound(self) -> str:
        return f"Staleness is bounded by the lease TTL (default: {self.default_ttl_ticks} ticks)."