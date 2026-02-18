from enum import Enum
from typing import Set, Tuple


class MESIState(Enum):
    """
    Stable MESI states, formally mapping to capability states.
    Source: Sorin, Hill, Wood — A Primer on Memory Consistency and Cache Coherence (2nd ed.), Ch. 6.4.1
    """
    MODIFIED = "Modified"       # Valid, exclusive, owned, dirty. The agent has delegated this capability, making the authority's copy stale. Only this agent's cache holds the current truth for its sub-tree.
    EXCLUSIVE = "Exclusive"     # Valid, exclusive, clean. The agent is the sole holder of this capability.
    SHARED = "Shared"           # Valid, not exclusive, clean. Multiple agents hold this capability.
    INVALID = "Invalid"         # Not valid. The capability has been revoked, expired, exhausted, or timed out from a transient state.


class TransientState(Enum):
    """
    Transient MESI states, representing in-flight transitions.
    Source: Primer, Ch. 6.4.1 (XYZ notation: from X, going to Y, waiting for Z).
    Per ADR-005, all transient states are subject to a fail-safe timeout.
    """
    ISG = "Invalid-to-Shared-waiting-Grant"
    IED = "Invalid-to-Exclusive-waiting-Delegation"
    EIA = "Exclusive-to-Invalid-waiting-Ack"
    SIA = "Shared-to-Invalid-waiting-Ack"
    MIC = "Modified-to-Invalid-waiting-Cascade"
    MIA = "Modified-to-Invalid-waiting-Ack"

# Valid state transitions for the MESI protocol
VALID_TRANSITIONS: Set[Tuple[MESIState, MESIState]] = {
    (MESIState.INVALID, MESIState.SHARED),
    (MESIState.INVALID, MESIState.EXCLUSIVE),
    (MESIState.SHARED, MESIState.INVALID),
    (MESIState.SHARED, MESIState.EXCLUSIVE),
    (MESIState.EXCLUSIVE, MESIState.SHARED),
    (MESIState.EXCLUSIVE, MESIState.MODIFIED),
    (MESIState.EXCLUSIVE, MESIState.INVALID),
    (MESIState.MODIFIED, MESIState.INVALID),
    (MESIState.MODIFIED, MESIState.SHARED),
}

def is_valid_transition(current_state: MESIState, next_state: MESIState) -> bool:
    """
    Checks if a transition between two MESI states is valid.
    """
    return (current_state, next_state) in VALID_TRANSITIONS
