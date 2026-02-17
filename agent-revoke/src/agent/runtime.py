from typing import Optional, List
from uuid import UUID

from core.clock import LogicalClock
from core.types import (
    RevocationEvent,
    ActionResult,
    ActionRecord,
    Capability,
    MESIState,
)
from agent.cache import CapabilityCache
from authority.service import AuthorityService


class AgentRuntime:
    def __init__(
        self,
        agent_id: UUID,
        authority: AuthorityService,
        cache: CapabilityCache,
        clock: LogicalClock,
    ):
        self.agent_id = agent_id
        self.authority = authority
        self.cache = cache
        self.clock = clock
        self.action_history: List[ActionRecord] = []

    def on_revocation(self, event: RevocationEvent) -> bool:
        self.cache.invalidate(event.capability_id)
        # Record the revocation event in the action history
        self.report_action(
            ActionRecord(
                agent_id=self.agent_id,
                resource=f"revocation:{event.reason.value}",
                result=ActionResult.ALLOWED,
                tick=self.clock.now(),
                capability_id=event.capability_id,
            )
        )
        return True

    def request_capability(self, resource: str) -> Optional[Capability]:
        return self.authority.grant_capability(self.agent_id, resource)

    def attempt_action(self, resource: str) -> ActionResult:
        cap = self.cache.get_by_resource(resource)
        if not cap:
            return ActionResult.DENIED

        if self.cache.expire_ttl(cap.id, self.clock.now()):
            return ActionResult.DENIED

        if cap.state == MESIState.INVALID:
            return ActionResult.DENIED

        exec_count_result = self.cache.check_exec_count(cap.id)
        if exec_count_result == ActionResult.EXHAUSTED:
            return ActionResult.EXHAUSTED

        self.cache.increment_ops(cap.id)
        
        action_record = ActionRecord(
            agent_id=self.agent_id,
            resource=resource,
            result=ActionResult.ALLOWED,
            tick=self.clock.now(),
            capability_id=cap.id,
        )
        self.report_action(action_record)

        return ActionResult.ALLOWED

    def attempt_write_action(self, resource: str) -> ActionResult:
        cap = self.cache.get_by_resource(resource)
        if not cap:
            return ActionResult.DENIED

        if self.cache.expire_ttl(cap.id, self.clock.now()):
            return ActionResult.DENIED

        if cap.state == MESIState.INVALID:
            return ActionResult.DENIED

        exec_count_result = self.cache.check_exec_count(cap.id)
        if exec_count_result == ActionResult.EXHAUSTED:
            return ActionResult.EXHAUSTED

        self.cache.increment_ops(cap.id)
        
        # Transition to Modified state on write
        self.cache.update_state(cap.id, MESIState.MODIFIED)

        action_record = ActionRecord(
            agent_id=self.agent_id,
            resource=resource,
            result=ActionResult.ALLOWED,
            tick=self.clock.now(),
            capability_id=cap.id,
        )
        self.report_action(action_record)

        return ActionResult.ALLOWED

    def report_action(self, action: ActionRecord) -> None:
        self.action_history.append(action)
        self.from authority.trust_scorer.check_anomaly(self.agent_id, self.action_history)

    def sync_capabilities(self) -> None:
        caps = self.from authority.registry.get_for_agent(self.agent_id)
        for cap in caps:
            cached_cap = self.cache.get(cap.id)
            if cached_cap:
                new_cap = Capability(**{**cap.__dict__, "operations_used": cached_cap.operations_used})
                self.cache.store(new_cap)
            else:
                self.cache.store(cap)
