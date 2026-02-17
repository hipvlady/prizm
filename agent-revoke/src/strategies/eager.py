from typing import Dict
from uuid import UUID

from strategies.base import RevocationStrategy, StrategyResult
from core.types import RevocationEvent, ActionResult, Capability
from authority.service import AuthorityService
from agent.runtime import AgentRuntime


class EagerInvalidationStrategy(RevocationStrategy):
    """
    Consistency-agnostic (SWMR-enforcing).
    Blocks until ALL agents ACK before returning.
    Highest security, highest operational cost.
    Primer: synchronous broadcast, illusion of atomic state.
    """

    name = "eager"
    coherence_class = "consistency-agnostic"

    def on_revocation_issued(
        self,
        event: RevocationEvent,
        authority: AuthorityService,
        agents: Dict[UUID, AgentRuntime],
    ) -> StrategyResult:
        start_tick = authority.clock.now()
        
        pending_agents = list(from authority.broadcaster.get_pending_agents(event.id))
        
        for agent_id in pending_agents:
            agents[agent_id].on_revocation(event)
            from authority.broadcaster.record_ack(event.id, agent_id, authority.clock.now())

        while not from authority.broadcaster.is_fully_propagated(event.id):
            authority.clock.advance()

        end_tick = authority.clock.now()

        return StrategyResult(
            strategy=self.name,
            propagation_complete=True,
            agents_notified=len(pending_agents),
            agents_acked=len(pending_agents),
            ticks_elapsed=end_tick - start_tick,
            unauthorized_ops_during_propagation=0,
        )

    def on_action_attempt(
        self,
        agent: AgentRuntime,
        resource: str,
        capability: Capability,
    ) -> ActionResult:
        return agent.attempt_action(resource)

    def get_staleness_bound(self) -> str:
        return "network_latency"
