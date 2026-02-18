from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from src.core.types import Capability, RevocationEvent, ActionRecord, ActionResult
from src.core.mesi import MESIState
from .cache import AgentCache

if TYPE_CHECKING:
    from src.authority.service import AuthorityService
    from src.strategies.base import RevocationStrategy
    from src.core.clock import LogicalClock

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
    ):
        self.agent_id = agent_id
        self.authority = authority
        self.strategy = strategy
        self.clock = clock
        self.cache = AgentCache(agent_id, transient_timeout_ticks)

    @property
    def state(self):
        return self.cache.state

    def on_revocation_received(self, event: RevocationEvent):
        """Hook for when the authority pushes a revocation event to this agent."""
        cap = self.cache.get(event.capability_id)
        if not cap:
            return

        updated_cap = self.strategy.on_revoke(self, event)
        if updated_cap:
            self.cache.update(updated_cap)

    def attempt_action(self, resource: str, tick: int) -> ActionRecord:
        """
        Attempts to perform an action, delegating all logic to the strategy.
        """
        cap = self.cache.find_by_resource(resource)
        if not cap:
            return self._record_action(None, resource, tick, False, ActionResult.DENIED_INVALID)

        # Delegate to strategy
        updated_cap = self.strategy.on_action(self, cap)
        self.cache.update(updated_cap)

        is_authorized = updated_cap.state not in [MESIState.INVALID] and updated_cap.transient_state is None
        
        result = ActionResult.ALLOWED if is_authorized else ActionResult.DENIED_INVALID
        if updated_cap.transient_state is not None:
            result = ActionResult.DENIED_TRANSIENT

        record = self._record_action(updated_cap, resource, tick, is_authorized, result)

        if is_authorized:
            self.cache.increment_ops(updated_cap.id)

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