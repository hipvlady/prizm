# Copyright (c) 2026 Prizm contributors.
"""MESI stable and transient states with transition validation."""

from __future__ import annotations

from enum import Enum
from typing import Set, Tuple


class MESIState(Enum):
    """Stable MESI states for capability coherence."""

    MODIFIED = "Modified"
    EXCLUSIVE = "Exclusive"
    SHARED = "Shared"
    INVALID = "Invalid"


class TransientState(Enum):
    """Transient MESI states using XYZ transition notation."""

    ISG = "Invalid-to-Shared-waiting-Grant"
    IED = "Invalid-to-Exclusive-waiting-Delegation"
    EIA = "Exclusive-to-Invalid-waiting-Ack"
    SIA = "Shared-to-Invalid-waiting-Ack"
    MIC = "Modified-to-Invalid-waiting-Cascade"
    MIA = "Modified-to-Invalid-waiting-Ack"


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
    """Validate whether a stable-state transition is allowed.

    Parameters
    ----------
    current_state : MESIState
        Source stable state.
    next_state : MESIState
        Target stable state.

    Returns
    -------
    bool
        ``True`` when transition is valid.
    """
    return (current_state, next_state) in VALID_TRANSITIONS
