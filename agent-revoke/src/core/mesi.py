# Copyright (c) 2026 Prizm contributors.
"""MESI stable and transient states with transition validation."""

from __future__ import annotations

from enum import Enum
from typing import Set, Tuple

from .exceptions import InvalidTransitionError


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


def transition_state(current_state: MESIState, next_state: MESIState) -> MESIState:
    """Validate and perform a stable MESI transition.

    Raises
    ------
    InvalidTransitionError
        If transition is not part of ``VALID_TRANSITIONS``.
    """
    if not is_valid_transition(current_state, next_state):
        raise InvalidTransitionError(current_state.value, next_state.value, "transition_state")
    return next_state


def can_act_in_transient(
    transient_state: TransientState,
    strategy_name: str,
    is_write: bool,
    *,
    lease_valid: bool = True,
    ops_remaining: bool = True,
) -> bool:
    """Evaluate whether an action is permitted in a transient state.

    Parameters
    ----------
    transient_state : TransientState
        Current transient state.
    strategy_name : str
        Strategy identifier (`eager`, `lazy`, `lease`, `exec_count`).
    is_write : bool
        Whether the action is a write operation.
    lease_valid : bool, optional
        Lease validity signal for lease strategy.
    ops_remaining : bool, optional
        Operation budget signal for exec-count strategy.
    """
    if transient_state in {TransientState.ISG, TransientState.IED}:
        return False

    if transient_state in {TransientState.EIA, TransientState.SIA}:
        if strategy_name == "eager":
            return False
        if strategy_name == "lazy":
            return True
        if strategy_name == "lease":
            return lease_valid
        if strategy_name == "exec_count":
            return ops_remaining
        return False

    if transient_state in {TransientState.MIC, TransientState.MIA}:
        return not is_write

    return False
