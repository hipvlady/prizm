from typing import Dict
from uuid import UUID

from strategies.base import RevocationStrategy, StrategyResult
from core.types import RevocationEvent, ActionResult, Capability
from authority.service import AuthorityService
from agent.runtime import AgentRuntime


class LeaseBasedStrategy(RevocationStrategy):
    """
    Consistency-directed. Temporal Coherence (Primer Ch.10 §10.1.3).
    Agent SELF-INVALIDATES on TTL expiry — writer does NOT push invalidation.
    Staleness bound: ttl_seconds.
    """

    name = "lease"
    coherence_class = "consistency-directed"
    
    def __init__(self, default_ttl_ticks: int = 600):
        self.default_ttl_ticks = default_ttl_ticks

    def on_revocation_issued(
        self,
        event: RevocationEvent,
        authority: AuthorityService,
        agents: Dict[UUID, AgentRuntime],
    ) -> StrategyResult:
        # In lease-based strategy, revocation is handled by TTL expiry on the agent side.
        # The authority still marks the capability as invalid.
        return StrategyResult(
            strategy=self.name,
            propagation_complete=False,
            agents_notified=0,
            agents_acked=0,
            ticks_elapsed=0,
            unauthorized_ops_during_propagation=0,
        )

    def on_action_attempt(
        self,
        agent: AgentRuntime,
        resource: str,
        capability: Capability,
    ) -> ActionResult:
        # The agent's attempt_action logic already handles TTL expiry.
        return agent.attempt_action(resource)

    def get_staleness_bound(self) -> str:
        return f"{self.default_ttl_ticks} ticks TTL"
