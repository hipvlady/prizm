from dataclasses import dataclass
from uuid import UUID

from core.types import MESIState, MESITransitionError, TransientState

TRANSITION_TABLE: dict[tuple[MESIState, str], MESIState] = {
    (MESIState.INVALID, "grant_exclusive"): MESIState.EXCLUSIVE,
    (MESIState.INVALID, "grant_shared"): MESIState.SHARED,
    (MESIState.EXCLUSIVE, "acquire_shared"): MESIState.SHARED,
    (MESIState.EXCLUSIVE, "write_hit"): MESIState.MODIFIED,
    (MESIState.EXCLUSIVE, "read_hit"): MESIState.EXCLUSIVE,
    (MESIState.EXCLUSIVE, "revoke"): MESIState.INVALID,
    (MESIState.EXCLUSIVE, "ttl_expired"): MESIState.INVALID,
    (MESIState.EXCLUSIVE, "count_exhausted"): MESIState.INVALID,
    (MESIState.SHARED, "invalidate"): MESIState.INVALID,
    (MESIState.SHARED, "write_hit"): MESIState.MODIFIED,
    (MESIState.SHARED, "read_hit"): MESIState.SHARED,
    (MESIState.SHARED, "revoke"): MESIState.INVALID,
    (MESIState.SHARED, "ttl_expired"): MESIState.INVALID,
    (MESIState.SHARED, "count_exhausted"): MESIState.INVALID,
    (MESIState.MODIFIED, "write_hit"): MESIState.MODIFIED,
    (MESIState.MODIFIED, "read_hit"): MESIState.MODIFIED,
    (MESIState.MODIFIED, "revoke"): MESIState.INVALID,
    (MESIState.MODIFIED, "ttl_expired"): MESIState.INVALID,
    (MESIState.MODIFIED, "count_exhausted"): MESIState.INVALID,
}


def transition(current: MESIState, event: str) -> MESIState:
    """Raises MESITransitionError for invalid transitions."""
    if (current, event) not in TRANSITION_TABLE:
        raise MESITransitionError(current, MESIState.INVALID, f"No transition for event '{event}'")
    return TRANSITION_TABLE[(current, event)]


def can_transition(current: MESIState, event: str) -> bool:
    return (current, event) in TRANSITION_TABLE


def is_valid_state(state: MESIState) -> bool:
    return isinstance(state, MESIState)


@dataclass
class TransientCapability:
    capability_id: UUID
    from_state: MESIState
    to_state: MESIState
    waiting_for: str  # "ACK", "LEASE_EXPIRY", "COUNT_BOUNDARY"
    transient_state: TransientState
    tick_entered: float
    timeout_ticks: int = 100
