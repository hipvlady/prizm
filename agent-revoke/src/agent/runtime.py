# Copyright (c) 2026 Prizm contributors.
"""Agent runtime (PEP) applying strategy-specific authorisation checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from src.core.exceptions import CacheMissError
from src.core.logging_utils import get_logger
from src.core.types import ActionRecord, Capability, RevocationEvent
from src.strategies.base import ActionResult

from .cache import AgentCache

if TYPE_CHECKING:
    from src.authority.service import AuthorityService
    from src.core.clock import LogicalClock
    from src.simulation.consistency import ConsistencyMonitor
    from src.simulation.metrics import MetricsCollector
    from src.strategies.base import RevocationStrategy

LOGGER = get_logger(__name__)


class AgentRuntime:
    """Policy Enforcement Point managing local capability cache and actions."""

    def __init__(
        self,
        agent_id: UUID,
        authority: AuthorityService,
        strategy: RevocationStrategy,
        clock: LogicalClock,
        transient_timeout_ticks: int,
        monitor: Optional[ConsistencyMonitor] = None,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """Initialise runtime dependencies.

        Parameters
        ----------
        agent_id : UUID
            Agent identifier.
        authority : AuthorityService
            Authority service for revalidation operations.
        strategy : RevocationStrategy
            Revocation strategy used for action validation.
        clock : LogicalClock
            Logical simulation clock.
        transient_timeout_ticks : int
            Fail-safe timeout for transient states.
        monitor : ConsistencyMonitor, optional
            Consistency monitor.
        metrics_collector : MetricsCollector, optional
            Metrics collector.
        """
        from src.simulation.consistency import ConsistencyMonitor
        from src.simulation.metrics import MetricsCollector

        self.agent_id = agent_id
        self.authority = authority
        self.strategy = strategy
        self.clock = clock
        self.monitor = monitor if monitor is not None else ConsistencyMonitor()
        self.metrics_collector = (
            metrics_collector if metrics_collector is not None else MetricsCollector()
        )
        self.cache = AgentCache(agent_id, transient_timeout_ticks, self.metrics_collector)

    @property
    def state(self):
        """Return local agent state object."""
        return self.cache.state

    def on_revocation_received(self, event: RevocationEvent, tick: Optional[int] = None):
        """Handle authority revocation event delivery.

        Parameters
        ----------
        event : RevocationEvent
            Revocation event payload.
        tick : int, optional
            Delivery tick. Uses current clock tick when omitted.
        """
        if not self.strategy.accepts_push_revocation:
            LOGGER.debug(
                "event=revocation_ignored strategy=%s agent=%s capability=%s",
                self.strategy.name,
                self.agent_id,
                event.capability_id,
            )
            return

        ack_tick = self.clock.now() if tick is None else tick
        self.monitor.record_agent_ack(self.agent_id, event.id, ack_tick)
        self.invalidate_capability(event.capability_id)
        LOGGER.info(
            "event=revocation_ack agent=%s event_id=%s capability=%s",
            self.agent_id,
            event.id,
            event.capability_id,
        )

    def invalidate_capability(self, capability_id: UUID):
        """Invalidate a capability in local cache."""
        self.cache.invalidate(capability_id)

    def attempt_action(self, resource: str, tick: int) -> ActionRecord:
        """Attempt an action against a resource.

        Parameters
        ----------
        resource : str
            Resource identifier.
        tick : int
            Current logical tick.

        Returns
        -------
        ActionRecord
            Recorded action with authorisation outcome.
        """
        try:
            cap = self.cache.find_by_resource(resource)
            if not cap:
                raise CacheMissError(self.agent_id, resource)
        except CacheMissError as exc:
            fallback_cap = self.cache.find_any_by_resource(resource)
            LOGGER.warning("event=cache_miss %s", exc)
            return self._record_action(
                fallback_cap, resource, tick, False, ActionResult.DENIED_INVALID
            )

        result = self.strategy.validate_action(self, cap)
        if result in (ActionResult.EXHAUSTED, ActionResult.EXPIRED):
            self.metrics_collector.record_revalidation()
            self.strategy.revalidate(self, cap)

        is_authorized = result == ActionResult.ALLOWED
        record = self._record_action(cap, resource, tick, is_authorized, result)
        if is_authorized:
            self.strategy.record_action(self, cap, record)
        return record

    def check_transient_timeouts(self, tick: int):
        """Check transient timeout fail-safe conditions.

        Parameters
        ----------
        tick : int
            Current logical tick.
        """
        self.cache.check_transient_timeouts(tick)

    def _record_action(
        self,
        cap: Optional[Capability],
        resource: str,
        tick: int,
        authorized: bool,
        result: ActionResult,
    ) -> ActionRecord:
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
