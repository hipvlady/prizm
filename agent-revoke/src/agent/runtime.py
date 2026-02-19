from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from src.core.types import Capability, RevocationEvent, ActionRecord
from src.strategies.base import ActionResult
from src.core.mesi import MESIState
from .cache import AgentCache

if TYPE_CHECKING:
    from src.authority.service import AuthorityService
    from src.strategies.base import RevocationStrategy
    from src.core.clock import LogicalClock
    from src.simulation.consistency import ConsistencyMonitor
    from src.simulation.metrics import MetricsCollector

class AgentRuntime:
    """
    The PEP (Policy Enforcement Point). It manages the agent's local state and
    delegates all authorization decisions to its configured RevocationStrategy.
    """
    def __init__(
        self,
        agent_id: UUID,
        authority: AuthorityService,
        strategy: RevocationStrategy,
        clock: LogicalClock,
        transient_timeout_ticks: int,
        monitor: ConsistencyMonitor,
        metrics_collector: MetricsCollector,
    ):
        self.agent_id = agent_id
        self.authority = authority
        self.strategy = strategy
        self.clock = clock
        self.cache = AgentCache(agent_id, transient_timeout_ticks, metrics_collector)
        self.monitor = monitor
        self.metrics_collector = metrics_collector

    @property
    def state(self):
        return self.cache.state

    def on_revocation_received(self, event: RevocationEvent, tick: int):
        """
        Hook for when the authority pushes a revocation event to this agent.
        The agent acknowledges the event and invalidates its local cache.
        """
        self.monitor.record_agent_ack(self.agent_id, event.id, tick)
        self.invalidate_capability(event.capability_id)

    def invalidate_capability(self, capability_id: UUID):
        """Invalidates a capability in the agent's cache."""
        self.cache.invalidate(capability_id)

    def attempt_action(self, resource: str, tick: int) -> ActionRecord:
        """
        Attempts to perform an action, delegating all logic to the strategy.
        Handles revalidation for expired or exhausted capabilities.
        """
        cap = self.cache.find_by_resource(resource)
        if not cap:
            return self._record_action(None, resource, tick, False, ActionResult.DENIED_INVALID)

        # 1. Delegate validation to the current strategy
        result = self.strategy.validate_action(self, cap)
        
        # 2. If exhausted or expired, attempt revalidation
        if result == ActionResult.EXHAUSTED or result == ActionResult.EXPIRED:
            self.metrics_collector.record_revalidation()
            new_cap = self.strategy.revalidate(self, cap)
            if new_cap:
                # Re-evaluate with the new capability
                result = self.strategy.validate_action(self, new_cap)
                cap = new_cap

        # 3. Determine final authorization status
        is_authorized = result == ActionResult.ALLOWED
        
        # 4. Record the action attempt locally
        record = self._record_action(cap, resource, tick, is_authorized, result)

        # 5. If authorized, let the strategy record the action (e.g., for op counting)
        if is_authorized:
            self.strategy.record_action(self, cap, record)

        return record

    def check_transient_timeouts(self, tick: int):
        """Delegates transient state timeout checks to the cache."""
        self.cache.check_transient_timeouts(tick)

    def _record_action(self, cap: Optional[Capability], resource: str, tick: int, authorized: bool, result: ActionResult) -> ActionRecord:
        record = ActionRecord(
            agent_id=self.agent_id,
            capability_id=cap.id if cap else None,
            resource=resource,
            tick=tick,
            authorized=authorized,
            result=result,
            delegation_depth=cap.delegation_depth if cap else -1,
        )
        self.state.action_history.append(record)
        return record