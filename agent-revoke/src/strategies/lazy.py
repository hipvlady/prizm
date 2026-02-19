from __future__ import annotations
from typing import TYPE_CHECKING, List

from .base import RevocationStrategy, CoherenceClass, BoundType, ActionResult, StrategyMetrics
from src.core.mesi import MESIState, TransientState
from src.core.types import Capability

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import RevocationEvent, ActionRecord


class LazyInvalidationStrategy(RevocationStrategy):
    """
    Consistency-Directed. Agent checks with authority on a defined interval ("check-on-use").
    The authority does not push revocations; the agent pulls validity information.
    """
    name: str = "lazy"
    coherence_class: CoherenceClass = CoherenceClass.CONSISTENCY_DIRECTED
    bound_type: BoundType = BoundType.TIME

    def __init__(self, check_interval_ticks: int = 100):
        self.check_interval_ticks = check_interval_ticks
        self._metrics = StrategyMetrics()

    def initiate_revocation(self, event: "RevocationEvent", agents: List["AgentRuntime"]) -> None:
        # In Lazy mode, the authority doesn't push revocations to agents.
        # This method is part of the ABC but is a no-op for lazy strategy.
        pass

    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """On action, check if the revalidation interval has passed."""
        if agent.clock.now() - agent.cache.state.last_sync_tick > self.check_interval_ticks:
            # Time to revalidate. Enter a transient state.
            agent.cache.enter_transient_state(capability.id, TransientState.ISG)
            return ActionResult.PENDING_VALIDATION
        
        if capability.state == MESIState.INVALID:
            return ActionResult.DENIED
            
        return ActionResult.ALLOWED

    def on_tick(self, agent: "AgentRuntime", tick: int) -> None:
        """Periodically re-validate capabilities based on the interval."""
        if tick - agent.cache.state.last_sync_tick > self.check_interval_ticks:
            for cap_id in list(agent.cache.state.capabilities.keys()):
                cap = agent.cache.get(cap_id)
                if cap and cap.state != MESIState.INVALID:
                    # This is a simplified model. A real implementation would batch these.
                    agent.cache.enter_transient_state(cap.id, TransientState.ISG, tick)
            agent.cache.state.last_sync_tick = tick

    def record_action(self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord") -> None:
        pass  # No specific recording logic for lazy

    def get_metrics(self) -> "StrategyMetrics":
        return self._metrics

    def get_theoretical_bound(self) -> str:
        return f"Staleness window is at most {self.check_interval_ticks} ticks."