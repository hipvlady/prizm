from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class MESITransitionError(Exception):
    def __init__(self, from_state: "MESIState", to_state: "MESIState", reason: str):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        super().__init__(f"Invalid MESI transition from {from_state} to {to_state}: {reason}")


class ScopeAttenuationError(Exception):
    def __init__(self, child_scope: tuple[str, ...], parent_scope: tuple[str, ...]):
        self.child_scope = child_scope
        self.parent_scope = parent_scope
        super().__init__(f"Child scope {child_scope} is not a subset of parent scope {parent_scope}")


class CapabilityExhaustedError(Exception):
    def __init__(self, capability_id: UUID, max_operations: int):
        self.capability_id = capability_id
        self.max_operations = max_operations
        super().__init__(f"Capability {capability_id} has been exhausted (max_operations: {max_operations})")


class MESIState(Enum):
    MODIFIED = "M"
    EXCLUSIVE = "E"
    SHARED = "S"
    INVALID = "I"


class TransientState(Enum):
    EIA = "EIA"  # Exclusive -> Invalid waiting ACK
    SIA = "SIA"  # Shared -> Invalid waiting ACK
    MIC = "MIC"  # Modified -> Invalid waiting ACK
    ISG = "ISG"  # Invalid -> Shared waiting Grant
    IED = "IED"  # Invalid -> Exclusive waiting Grant
    MIA = "MIA"  # Modified -> Invalid waiting ACK


class RevocationReason(Enum):
    EXPLICIT = "EXPLICIT"
    EXPIRED = "EXPIRED"
    EXHAUSTED = "EXHAUSTED"
    PARENT_REVOKED = "PARENT_REVOKED"
    TRUST_VIOLATION = "TRUST_VIOLATION"
    COMPROMISED = "COMPROMISED"


class ActionResult(Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    EXHAUSTED = "EXHAUSTED"


@dataclass(frozen=True)
class Capability:
    id: UUID
    agent_id: UUID
    resource: str
    state: MESIState
    granted_at: float  # simulation tick
    expires_at: Optional[float] = None  # lease TTL in ticks (None = no lease)
    max_operations: Optional[int] = None  # exec-count bound (None = unbounded, NOT zero)
    operations_used: int = 0
    delegator_id: Optional[UUID] = None
    parent_cap_id: Optional[UUID] = None
    scope: tuple[str, ...] = ()  # tuple for frozen dataclass compatibility
    trust_score: float = 1.0
    version: int = 0


@dataclass(frozen=True)
class RevocationEvent:
    id: UUID
    capability_id: UUID
    reason: RevocationReason
    issued_at: float
    cascade: bool = False


@dataclass(frozen=True)
class ActionRecord:
    agent_id: UUID
    resource: str
    result: ActionResult
    tick: float
    capability_id: Optional[UUID] = None
