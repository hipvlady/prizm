from typing import Dict
from uuid import UUID

from strategies.base import RevocationStrategy, StrategyResult
from core.types import RevocationEvent, ActionResult, Capability
from authority.service import AuthorityService
from agent.runtime import AgentRuntime


class ExecCountBoundedStrategy(RevocationStrategy):
    """
    Consistency-directed. RCC acquire pattern (Primer Ch.10 §10.1.4).
    Agent gets N operations max. Re-validates at Exhausted boundary.
    Staleness bound: max_operations - operations_at_revocation (in OPS, not time).
    
    KILLER DEMO: N=50 → exactly 50 unauthorized ops.
    Compare: TTL(60s) @ 100ops/sec → up to 6000 unauthorized ops.
    """

    name = "exec_count"
    coherence_class = "consistency-directed"

    def __init__(self, max_operations: int = 50):
        self.max_operations = max_operations

    def on_revocation_issued(
        self,
        event: RevocationEvent,
        authority: AuthorityService,
        agents: Dict[UUID, AgentRuntime],
    ) -> StrategyResult:
        # Similar to lazy, the agent finds out upon exhaustion.
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
        result = agent.attempt_action(resource)
        if result == ActionResult.EXHAUSTED:
            agent.sync_capabilities()
        return result

    def get_staleness_bound(self) -> str:
        return f"N={self.max_operations} ops (vs TTL bound in time)"
