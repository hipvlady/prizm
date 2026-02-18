from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List
from uuid import UUID, uuid4

from .mesi import MESIState, TransientState


class RevocationReason(Enum):
    """The reason for a capability's invalidation."""
    EXPLICIT = "explicit"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    PARENT_REVOKED = "parent_revoked"
    TRUST_VIOLATION = "trust_violation"
    COMPROMISED = "compromised"
    TIMEOUT_FAILSAFE = "transient_state_timeout"  # ADR-005
    REVALIDATING = "revalidating"


class ActionResult(Enum):
    """The result of an agent's attempted action."""
    ALLOWED = "allowed"
    DENIED_INVALID = "denied_invalid_state"
    DENIED_TRANSIENT = "denied_transient_state"
    DENIED_SCOPE = "denied_scope_mismatch"
    PENDING_REVALIDATION = "pending_revalidation" # For RCC 'acquire' cycle
    EXPIRED = "expired"                          # For Temporal Coherence self-invalidation
    EXHAUSTED = "exhausted"                      # For RCC 'release' cycle
    TIMED_OUT = "timed_out"                      # ADR-005


class ScopeAttenuationError(Exception):
    """Raised when a delegation attempt violates the scope attenuation invariant."""
    def __init__(self, child_scope: tuple[str, ...], parent_scope: tuple[str, ...]):
        super().__init__(f"Child scope {child_scope} must be a subset of parent scope {parent_scope}")
        self.child_scope = child_scope
        self.parent_scope = parent_scope


class CapabilityExhaustedError(Exception):
    """Raised when an agent attempts to use a capability that has been exhausted (e.g., max_operations)."""
    pass


@dataclass(frozen=True)
class Capability:
    """
    A capability held by an agent, modeled as a cache line in a coherence protocol.
    This object is immutable (`frozen=True`); state changes result in a new instance.
    """
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
    trust_score: float = 1.0
    version: int = 0
    transient_state: Optional[TransientState] = None
    transient_entered_tick: Optional[int] = None
    delegation_depth: int = 0

    def to_dict(self) -> dict:
        """Helper to convert dataclass to dict for creating new instances."""
        return {
            "id": self.id, "agent_id": self.agent_id, "resource": self.resource,
            "state": self.state, "granted_tick": self.granted_tick,
            "expires_tick": self.expires_tick, "max_operations": self.max_operations,
            "operations_used": self.operations_used, "delegator_id": self.delegator_id,
            "parent_cap_id": self.parent_cap_id, "scope": self.scope,
            "trust_score": self.trust_score, "version": self.version,
            "transient_state": self.transient_state,
            "transient_entered_tick": self.transient_entered_tick,
            "delegation_depth": self.delegation_depth,
        }


@dataclass(frozen=True)
class RevocationEvent:
    """An event representing the revocation of a capability, sent from PDP to PEP."""
    capability_id: UUID
    reason: RevocationReason
    issued_tick: int
    id: UUID = field(default_factory=uuid4)
    cascade: bool = False
    propagate_to: List[UUID] = field(default_factory=list)


@dataclass(frozen=True)
class ActionRecord:
    """A record of an action attempted by an agent."""
    agent_id: UUID
    capability_id: Optional[UUID]
    resource: str
    tick: int
    authorized: bool
    result: ActionResult
    delegation_depth: int


@dataclass
class AgentState:
    """The complete state of a single agent, managed by the AgentRuntime."""
    agent_id: UUID
    capabilities: Dict[UUID, Capability] = field(default_factory=dict)
    trust_score: float = 1.0
    action_history: List[ActionRecord] = field(default_factory=list)
    last_sync_tick: int = 0
    heartbeat_tick: int = 0
