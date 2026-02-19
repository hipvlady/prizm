# Copyright (c) 2026 Prizm contributors.
"""Core dataclasses and enums shared across simulation modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from ..strategies.base import ActionResult
from .mesi import MESIState, TransientState


class RevocationReason(Enum):
    """Reason for capability invalidation."""

    EXPLICIT = "explicit"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    PARENT_REVOKED = "parent_revoked"
    TRUST_VIOLATION = "trust_violation"
    COMPROMISED = "compromised"
    TIMEOUT_FAILSAFE = "transient_state_timeout"
    REVALIDATING = "revalidating"


class ScopeAttenuationError(Exception):
    """Raised when delegated scope is broader than parent scope."""

    def __init__(self, child_scope: tuple[str, ...], parent_scope: tuple[str, ...]):
        super().__init__(f"Child scope {child_scope} must be a subset of parent scope {parent_scope}")
        self.child_scope = child_scope
        self.parent_scope = parent_scope


class CapabilityExhaustedError(Exception):
    """Raised when operation budget is exhausted."""


@dataclass(frozen=True)
class DelegationPolicy:
    """Delegation guardrails for depth and operation budget propagation."""

    max_depth: int = 16
    require_scope_subset: bool = True
    propagate_remaining_ops: bool = True


@dataclass(frozen=True)
class Capability:
    """Immutable capability model used as coherence cache line analogue."""

    agent_id: UUID
    resource: str
    state: MESIState
    granted_tick: int
    id: UUID = field(default_factory=uuid4)
    expires_tick: Optional[int] = None
    max_operations: Optional[int] = None
    operations_used: int = 0
    delegator_id: Optional[UUID] = None
    parent_cap_id: Optional[UUID] = None
    scope: tuple[str, ...] = ()
    trust_score: float = 0.8
    version: int = 0
    transient_state: Optional[TransientState] = None
    transient_entered_tick: Optional[int] = None
    delegation_depth: int = 0

    def to_dict(self) -> dict:
        """Serialise capability to mutable dictionary for state updates."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "resource": self.resource,
            "state": self.state,
            "granted_tick": self.granted_tick,
            "expires_tick": self.expires_tick,
            "max_operations": self.max_operations,
            "operations_used": self.operations_used,
            "delegator_id": self.delegator_id,
            "parent_cap_id": self.parent_cap_id,
            "scope": self.scope,
            "trust_score": self.trust_score,
            "version": self.version,
            "transient_state": self.transient_state,
            "transient_entered_tick": self.transient_entered_tick,
            "delegation_depth": self.delegation_depth,
        }


@dataclass(frozen=True)
class RevocationEvent:
    """Revocation event propagated from PDP to PEP."""

    capability_id: UUID
    reason: RevocationReason
    issued_tick: int
    id: UUID = field(default_factory=uuid4)
    root_capability_id: Optional[UUID] = None
    cascade: bool = False
    propagated: Dict[UUID, Optional[int]] = field(default_factory=dict)
    expected_capabilities: Set[UUID] = field(default_factory=set)
    invalidated_capabilities: Set[UUID] = field(default_factory=set)
    cascade_completion_tick: Optional[int] = None


@dataclass(frozen=True)
class ActionRecord:
    """Recorded action attempt with authorisation outcome."""

    agent_id: UUID
    capability_id: Optional[UUID]
    resource: str
    tick: int
    authorized: bool
    result: ActionResult
    delegation_depth: int


@dataclass
class AgentState:
    """Mutable aggregate state for one runtime agent."""

    agent_id: UUID
    capabilities: Dict[UUID, Capability] = field(default_factory=dict)
    trust_score: float = 0.8
    action_history: List[ActionRecord] = field(default_factory=list)
    last_sync_tick: int = 0
    heartbeat_tick: int = 0
