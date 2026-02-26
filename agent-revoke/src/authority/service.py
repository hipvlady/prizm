# Copyright (c) 2026 Prizm contributors.
"""Authority service (PDP) for grant, delegation, and revocation flows."""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.authority.broadcaster import RevocationBroadcaster
from src.authority.registry import CapabilityRegistry
from src.authority.trust_scorer import TrustScorer
from src.core.clock import LogicalClock
from src.core.exceptions import (
    DelegationDepthExceededError,
    RemainingOpsPropagationError,
    RevocationError,
)
from src.core.logging_utils import get_logger
from src.core.types import (
    Capability,
    DelegationPolicy,
    MESIState,
    RevocationEvent,
    RevocationReason,
    ScopeAttenuationError,
)
from src.simulation.consistency import ConsistencyMonitor

LOGGER = get_logger(__name__)


class AuthorityService:
    """Policy Decision Point for capability lifecycle management."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        broadcaster: RevocationBroadcaster,
        trust_scorer: TrustScorer,
        clock: LogicalClock,
        monitor: Optional[ConsistencyMonitor] = None,
        delegation_policy: Optional[DelegationPolicy] = None,
    ):
        """Initialise authority service dependencies.

        Parameters
        ----------
        registry : CapabilityRegistry
            Canonical capability store.
        broadcaster : RevocationBroadcaster
            Event broadcaster for revocation notifications.
        trust_scorer : TrustScorer
            Behaviour scoring component.
        clock : LogicalClock
            Simulation logical clock.
        monitor : ConsistencyMonitor, optional
            Consistency monitor instance, by default a new one.
        """
        self.registry = registry
        self.broadcaster = broadcaster
        self.trust_scorer = trust_scorer
        self.clock = clock
        self.monitor = monitor if monitor is not None else ConsistencyMonitor()
        self.delegation_policy = delegation_policy if delegation_policy is not None else DelegationPolicy()

    def set_delegation_policy(self, policy: DelegationPolicy) -> None:
        """Update delegation policy at runtime.

        Parameters
        ----------
        policy : DelegationPolicy
            Policy containing depth and propagation constraints.
        """
        self.delegation_policy = policy

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
        """Grant a capability to an agent.

        Parameters
        ----------
        agent_id : UUID
            Agent identifier.
        resource : str
            Resource identifier.
        ttl : float, optional
            Lease duration in ticks.
        max_operations : int, optional
            Maximum operation budget for exec-count mode.
        scope : list[str], optional
            Capability scope.
        delegator_id : UUID, optional
            Delegator agent identifier.
        parent_cap_id : UUID, optional
            Parent capability for delegation chains.

        Returns
        -------
        Capability
            Granted capability object.
        """
        expires_at = self.clock.now() + ttl if ttl is not None else None
        parent = self.registry.get(parent_cap_id) if parent_cap_id else None
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
            delegation_depth=(parent.delegation_depth + 1) if parent is not None else 0,
        )
        self.registry.store(cap)
        LOGGER.info(
            "event=grant agent=%s capability=%s resource=%s",
            agent_id,
            cap.id,
            resource,
        )
        return cap

    def revoke_capability(
        self,
        capability_id: UUID,
        reason: RevocationReason,
        cascade: bool = False,
        *,
        completion_semantics: str = "push",
    ) -> RevocationEvent:
        """Revoke a capability and optionally cascade through descendants.

        Parameters
        ----------
        capability_id : UUID
            Capability to revoke.
        reason : RevocationReason
            Revocation reason.
        cascade : bool, optional
            Whether to revoke descendants, by default ``False``.
        completion_semantics : str, optional
            Revocation completion mode tag (``push``, ``pull_eventual``, or ``mixed``).

        Returns
        -------
        RevocationEvent
            Emitted revocation event.

        Raises
        ------
        RevocationError
            If the capability does not exist or state update fails.
        """
        event = RevocationEvent(
            id=uuid4(),
            capability_id=capability_id,
            reason=reason,
            issued_tick=self.clock.now(),
            root_capability_id=capability_id,
            cascade=cascade,
            completion_semantics=completion_semantics,
        )

        cap = self.registry.get(capability_id)
        if not cap:
            raise RevocationError(capability_id, "not found")

        try:
            cap_data = cap.to_dict()
            cap_data["state"] = MESIState.INVALID
            cap_data["version"] = cap.version + 1
            cap_data["transient_state"] = None
            cap_data["transient_entered_tick"] = None
            self.registry.update(Capability(**cap_data))
        except Exception as exc:
            raise RevocationError(capability_id, "failed to invalidate parent capability") from exc

        agents_to_notify = {cap.agent_id}
        expected_capabilities = {cap.id}

        for sibling in self.registry.list_by_agent_resource(cap.agent_id, cap.resource):
            if sibling.id == cap.id or sibling.state == MESIState.INVALID:
                continue
            expected_capabilities.add(sibling.id)
            sibling_data = sibling.to_dict()
            sibling_data["state"] = MESIState.INVALID
            sibling_data["version"] = sibling.version + 1
            sibling_data["transient_state"] = None
            sibling_data["transient_entered_tick"] = None
            self.registry.update(Capability(**sibling_data))

        if cascade:
            descendants = self.registry.get_delegation_chain(capability_id)
            for descendant in descendants:
                expected_capabilities.add(descendant.id)
                child_data = descendant.to_dict()
                child_data["state"] = MESIState.INVALID
                child_data["version"] = descendant.version + 1
                child_data["transient_state"] = None
                child_data["transient_entered_tick"] = None
                self.registry.update(Capability(**child_data))
                agents_to_notify.add(descendant.agent_id)

        event.expected_capabilities.update(expected_capabilities)

        self.monitor.record_revocation_broadcast(event, set(agents_to_notify))
        self.broadcaster.broadcast(event, list(agents_to_notify))
        LOGGER.info(
            "event=revoke capability=%s reason=%s cascade=%s recipients=%d",
            capability_id,
            reason.value,
            cascade,
            len(agents_to_notify),
        )
        return event

    def delegate_capability(
        self, from_agent_id: UUID, to_agent_id: UUID, parent_cap_id: UUID, attenuated_scope: List[str]
    ) -> Capability:
        """Delegate a capability with scope attenuation.

        Parameters
        ----------
        from_agent_id : UUID
            Delegating agent identifier.
        to_agent_id : UUID
            Recipient agent identifier.
        parent_cap_id : UUID
            Parent capability identifier.
        attenuated_scope : list[str]
            Delegated scope, must be subset of parent scope.

        Returns
        -------
        Capability
            Delegated capability.

        Raises
        ------
        RevocationError
            If parent capability cannot be found.
        DelegationDepthExceededError
            If delegation exceeds configured maximum depth.
        RemainingOpsPropagationError
            If parent has no remaining operation budget to propagate.
        ScopeAttenuationError
            If delegated scope exceeds parent scope.
        """
        parent_cap = self.registry.get(parent_cap_id)
        if not parent_cap:
            raise RevocationError(parent_cap_id, "parent capability not found")

        if self.delegation_policy.require_scope_subset and not set(attenuated_scope).issubset(
            set(parent_cap.scope)
        ):
            raise ScopeAttenuationError(tuple(attenuated_scope), parent_cap.scope)

        remaining_ops = None
        remaining_ttl = None
        child_depth = parent_cap.delegation_depth + 1
        if child_depth > self.delegation_policy.max_depth:
            raise DelegationDepthExceededError(
                parent_capability_id=parent_cap.id,
                parent_depth=parent_cap.delegation_depth,
                max_depth=self.delegation_policy.max_depth,
            )

        if self.delegation_policy.propagate_remaining_ops and parent_cap.max_operations is not None:
            remaining_ops = parent_cap.max_operations - parent_cap.operations_used
            if remaining_ops < 0:
                raise RemainingOpsPropagationError(
                    parent_cap.id,
                    "remaining operations became negative; parent state is inconsistent",
                )
            if remaining_ops == 0:
                raise RemainingOpsPropagationError(
                    parent_cap.id,
                    "cannot delegate exhausted capability (remaining operations == 0)",
                )

        if parent_cap.expires_tick is not None:
            remaining_ttl = max(0, parent_cap.expires_tick - self.clock.now())

        child = self.grant_capability(
            agent_id=to_agent_id,
            resource=parent_cap.resource,
            scope=attenuated_scope,
            ttl=remaining_ttl,
            max_operations=remaining_ops,
            delegator_id=from_agent_id,
            parent_cap_id=parent_cap_id,
        )
        LOGGER.info(
            "event=delegate from_agent=%s to_agent=%s parent=%s child=%s",
            from_agent_id,
            to_agent_id,
            parent_cap_id,
            child.id,
        )
        return child

    def check_capability(self, agent_id: UUID, resource: str) -> Dict:
        """Check whether an agent currently holds a valid capability.

        Parameters
        ----------
        agent_id : UUID
            Agent identifier.
        resource : str
            Resource identifier.

        Returns
        -------
        dict
            Validation payload including validity, state, and remaining bounds.
        """
        cap = self.registry.find_by_agent_resource(agent_id, resource)
        if cap is None:
            return {"valid": False, "state": MESIState.INVALID.value}

        if cap.state == MESIState.INVALID:
            return {"valid": False, "state": cap.state.value}

        if cap.expires_tick is not None and self.clock.now() >= cap.expires_tick:
            return {"valid": False, "state": MESIState.INVALID.value, "ttl_remaining": 0}

        remaining_ops = None
        if cap.max_operations is not None:
            remaining_ops = max(0, cap.max_operations - cap.operations_used)

        ttl_remaining = None
        if cap.expires_tick is not None:
            ttl_remaining = max(0, cap.expires_tick - self.clock.now())

        return {
            "valid": True,
            "state": cap.state.value,
            "remaining_ops": remaining_ops,
            "ttl_remaining": ttl_remaining,
        }

    def get_revocation_status(self, event_id: UUID) -> Dict:
        """Return pending ACK status for a revocation event.

        Parameters
        ----------
        event_id : UUID
            Revocation event identifier.

        Returns
        -------
        dict
            Event status payload with delivery and local-completion phases.
        """
        pending_count = self.monitor.get_pending_ack_count(event_id)
        expected_capabilities = self.monitor.get_expected_capabilities(event_id)
        invalidated_capabilities = self.monitor.get_invalidated_capabilities(event_id)
        cascade_completion_tick = self.monitor.get_cascade_completion_tick(event_id)
        delivery_completion_tick = self.monitor.get_delivery_completion_tick(event_id)
        return {
            "event_id": event_id,
            "completion_semantics": self.monitor.get_completion_semantics(event_id),
            "pending_acks": pending_count,
            "propagated": self.monitor.get_propagation_map(event_id),
            "cascade_completeness_ratio": self.monitor.get_cascade_completeness_ratio(event_id),
            "delivery_completion_tick": delivery_completion_tick,
            "delivery_complete": pending_count == 0,
            "cascade_completion_tick": cascade_completion_tick,
            "local_cascade_complete": cascade_completion_tick is not None,
            "expected_capabilities": expected_capabilities,
            "invalidated_capabilities": invalidated_capabilities,
            "pending_capabilities": len(expected_capabilities - invalidated_capabilities),
        }
