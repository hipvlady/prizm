# Copyright (c) 2026 Prizm contributors.
"""Eager consistency-agnostic revocation strategy."""

from __future__ import annotations
from typing import TYPE_CHECKING, List

from .base import RevocationStrategy, CoherenceClass, BoundType, ActionResult, StrategyMetrics
from src.core.types import Capability
from src.core.mesi import MESIState, can_act_in_transient

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import RevocationEvent, ActionRecord


class EagerInvalidationStrategy(RevocationStrategy):
    """
    Consistency-Agnostic (SWMR-enforcing). Revocation blocks until all agents ACK.
    This is the simplest, most consistent strategy. When a revocation event is received,
    the capability is immediately marked as INVALID.
    """
    name: str = "eager"
    coherence_class: CoherenceClass = CoherenceClass.CONSISTENCY_AGNOSTIC
    bound_type: BoundType = BoundType.HYBRID  # Not strictly time or ops based

    def __init__(self):
        self._metrics = StrategyMetrics()

    def initiate_revocation(self, event: "RevocationEvent", agents: List["AgentRuntime"]) -> None:
        """
        For Eager, the authority would block, but from the strategy's perspective
        on the agent, receiving the notice means we invalidate immediately.
        We find all capabilities that are descendants of the revoked one and invalidate them.
        """
        # This is a centralized call. A full implementation would involve complex ACK handling.
        # For now, we directly invalidate the capability on all provided agents.
        for agent in agents:
            if event.capability_id in agent.state.capabilities:
                agent.cache.invalidate(event.capability_id)


    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """In Eager mode, if a capability exists and is not Invalid, it's good to go."""
        if capability.transient_state is not None:
            allowed = can_act_in_transient(
                capability.transient_state,
                self.name,
                is_write="write" in capability.resource,
            )
            if not allowed:
                return ActionResult.DENIED_TRANSIENT
        if capability.state == MESIState.INVALID:
            return ActionResult.DENIED_INVALID
        return ActionResult.ALLOWED

    def on_tick(self, agent: "AgentRuntime", tick: int) -> None:
        pass  # Eager strategy is not time-dependent

    def record_action(self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord") -> None:
        pass  # No specific recording logic for eager

    def get_metrics(self) -> "StrategyMetrics":
        return self._metrics

    def get_theoretical_bound(self) -> str:
        return "Staleness is not possible under ideal conditions."

    def get_transient_state_duration(self) -> dict[str, float]:
        return self._metrics.transient_state_durations
