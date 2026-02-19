# Copyright (c) 2026 Prizm contributors.
"""Execution-count (RCC-like) revocation strategy."""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from .base import RevocationStrategy, CoherenceClass, BoundType, ActionResult, StrategyMetrics
from src.core.mesi import MESIState, TransientState
from src.core.types import Capability

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import RevocationEvent, ActionRecord


class ExecCountStrategy(RevocationStrategy):
    """
    Release Consistency-directed Coherence (RCC). Agent self-invalidates after a
    maximum number of operations. It is clock-independent.
    """
    name: str = "exec_count"
    coherence_class: CoherenceClass = CoherenceClass.CONSISTENCY_DIRECTED
    bound_type: BoundType = BoundType.OPERATIONS

    def __init__(self, max_operations: int = 50):
        self.max_operations = max_operations
        self._metrics = StrategyMetrics()

    def initiate_revocation(self, event: "RevocationEvent", agents: List["AgentRuntime"]) -> None:
        # Authority can still send an out-of-band revocation.
        # The generic `on_revocation_received` in AgentRuntime will handle it.
        pass

    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """
        This is the "release" part of the RCC cycle.
        If the operation count is exhausted, the capability must be re-acquired.
        """
        if capability.state == MESIState.INVALID:
            return ActionResult.DENIED_INVALID

        # The check is `operations_used < max_operations`.
        # When `operations_used == max_operations`, it's exhausted.
        if capability.max_operations is not None and capability.operations_used >= capability.max_operations:
            agent.cache.enter_transient_state(capability.id, TransientState.ISG, agent.clock.now())
            return ActionResult.EXHAUSTED

        return ActionResult.ALLOWED

    def on_tick(self, agent: "AgentRuntime", tick: int) -> None:
        pass  # Exec-count strategy is not time-dependent

    def record_action(self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord") -> None:
        """Post-action hook: increment counters."""
        agent.cache.increment_ops(capability.id)

    def revalidate(self, agent: "AgentRuntime", capability: "Capability") -> Optional["Capability"]:
        """
        Invalidates the exhausted capability and requests a new one from the authority.
        """
        agent.invalidate_capability(capability.id)
        status = agent.authority.check_capability(agent.agent_id, capability.resource)
        if not status.get("valid", False):
            return None
        new_cap = agent.authority.grant_capability(
            agent_id=agent.agent_id,
            resource=capability.resource,
            scope=capability.scope,
            max_operations=self.max_operations,
        )
        if new_cap:
            agent.cache.update(new_cap)
        return new_cap

    def get_metrics(self) -> "StrategyMetrics":
        return self._metrics

    def get_theoretical_bound(self) -> str:
        return f"Staleness is bounded by a maximum of {self.max_operations} operations."
