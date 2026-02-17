from typing import Dict
from uuid import UUID

from strategies.base import RevocationStrategy, StrategyResult
from core.types import RevocationEvent, ActionResult, Capability
from authority.service import AuthorityService
from agent.runtime import AgentRuntime


class LazyInvalidationStrategy(RevocationStrategy):
    """
    Consistency-directed.
    Revocation recorded at authority. Agent checks on NEXT action attempt.
    Staleness bound: network_latency + check_interval.
    """

    name = "lazy"
    coherence_class = "consistency-directed"

    def __init__(self, check_interval_ticks: int = 10):
        self.check_interval_ticks = check_interval_ticks
        self.last_check: Dict[UUID, int] = {}

    def on_revocation_issued(
        self,
        event: RevocationEvent,
        authority: AuthorityService,
        agents: Dict[UUID, AgentRuntime],
    ) -> StrategyResult:
        # In lazy strategy, we just record the revocation at the authority.
        # The agents will find out on their next action attempt.
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
        now = agent.clock.now()
        last_check_tick = self.last_check.get(agent.agent_id, 0)

        if now - last_check_tick >= self.check_interval_ticks:
            agent.sync_capabilities()
            self.last_check[agent.agent_id] = now

        return agent.attempt_action(resource)

    def get_staleness_bound(self) -> str:
        return f"check_interval ({self.check_interval_ticks} ticks)"
