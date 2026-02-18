from typing import Optional, List, Dict
from uuid import UUID, uuid4

from src.core.clock import LogicalClock
from src.core.types import (
    Capability,
    RevocationEvent,
    MESIState,
    RevocationReason,
    ScopeAttenuationError,
)
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer


class AuthorityService:
    def __init__(
        self,
        registry: CapabilityRegistry,
        broadcaster: RevocationBroadcaster,
        trust_scorer: TrustScorer,
        clock: LogicalClock,
    ):
        self.registry = registry
        self.broadcaster = broadcaster
        self.trust_scorer = trust_scorer
        self.clock = clock

    def grant_capability(
        self,
        agent_id: UUID,
        resource: str,
        *,
        ttl: Optional[float] = None,
        max_operations: Optional[int] = None,
        scope: Optional[List[str]] = None,
        delegator_id: Optional[UUID] = None,
        parent_cap_id: Optional[UUID] = None,
    ) -> Capability:
        expires_at = self.clock.now() + ttl if ttl else None
        cap = Capability(
            id=uuid4(),
            agent_id=agent_id,
            resource=resource,
            state=MESIState.EXCLUSIVE,
            granted_tick=self.clock.now(),
            expires_tick=expires_at,
            max_operations=max_operations,
            scope=tuple(scope) if scope else (),
            delegator_id=delegator_id,
            parent_cap_id=parent_cap_id,
        )
        self.registry.store(cap)
        return cap

    def revoke_capability(
        self, capability_id: UUID, reason: RevocationReason, cascade: bool = False
    ) -> RevocationEvent:
        event = RevocationEvent(
            id=uuid4(),
            capability_id=capability_id,
            reason=reason,
            issued_tick=self.clock.now(),
            cascade=cascade,
        )
        
        cap = self.registry.get(capability_id)
        if not cap:
            raise ValueError(f"Capability {capability_id} not found")

        agents_to_notify = [cap.agent_id]

        if cascade:
            descendants = self.registry.get_delegation_chain(capability_id)
            for descendant in descendants:
                agents_to_notify.append(descendant.agent_id)
        
        self.broadcaster.broadcast(event, agents_to_notify)
        return event

    def delegate_capability(
        self, from_agent_id: UUID, to_agent_id: UUID, parent_cap_id: UUID, attenuated_scope: List[str]
    ) -> Capability:
        parent_cap = self.registry.get(parent_cap_id)
        if not parent_cap:
            raise ValueError(f"Parent capability {parent_cap_id} not found")

        if not set(attenuated_scope).issubset(set(parent_cap.scope)):
            raise ScopeAttenuationError(tuple(attenuated_scope), parent_cap.scope)

        remaining_ops = None
        if parent_cap.max_operations is not None:
            remaining_ops = parent_cap.max_operations - parent_cap.operations_used

        return self.grant_capability(
            agent_id=to_agent_id,
            resource=parent_cap.resource,
            scope=attenuated_scope,
            max_operations=remaining_ops,
            delegator_id=from_agent_id,
            parent_cap_id=parent_cap_id,
        )

