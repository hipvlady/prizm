import pytest
from src.core.mesi import (
    InvalidTransitionError,
    MESIState,
    TransientState,
    can_act_in_transient,
    is_valid_transition,
    transition_state,
)

# Test cases for valid transitions
@pytest.mark.parametrize("from_state, to_state", [
    (MESIState.INVALID, MESIState.SHARED),
    (MESIState.INVALID, MESIState.EXCLUSIVE),
    (MESIState.SHARED, MESIState.INVALID),
    (MESIState.SHARED, MESIState.EXCLUSIVE),
    (MESIState.EXCLUSIVE, MESIState.SHARED),
    (MESIState.EXCLUSIVE, MESIState.MODIFIED),
    (MESIState.EXCLUSIVE, MESIState.INVALID),
    (MESIState.MODIFIED, MESIState.INVALID),
    (MESIState.MODIFIED, MESIState.SHARED),
])
def test_valid_transitions(from_state, to_state):
    """
    Tests that the MESI state machine allows valid transitions.
    """
    assert is_valid_transition(from_state, to_state) is True

# Test cases for invalid transitions
@pytest.mark.parametrize("from_state, to_state", [
    (MESIState.INVALID, MESIState.MODIFIED),
    (MESIState.SHARED, MESIState.MODIFIED),
    (MESIState.MODIFIED, MESIState.EXCLUSIVE),
    # Any transition to itself is invalid in this model
    (MESIState.INVALID, MESIState.INVALID),
    (MESIState.SHARED, MESIState.SHARED),
    (MESIState.EXCLUSIVE, MESIState.EXCLUSIVE),
    (MESIState.MODIFIED, MESIState.MODIFIED),
])
def test_invalid_transitions(from_state, to_state):
    """
    Tests that the MESI state machine rejects invalid transitions.
    """
    assert is_valid_transition(from_state, to_state) is False


def test_transition_state_raises_on_invalid_transition():
    with pytest.raises(InvalidTransitionError):
        transition_state(MESIState.INVALID, MESIState.MODIFIED)


@pytest.mark.parametrize(
    "strategy_name, lease_valid, ops_remaining, expected",
    [
        ("eager", True, True, False),
        ("lazy", True, True, True),
        ("lease", False, True, False),
        ("lease", True, True, True),
        ("exec_count", True, False, False),
        ("exec_count", True, True, True),
    ],
)
def test_transient_invalidation_action_gate(strategy_name, lease_valid, ops_remaining, expected):
    assert (
        can_act_in_transient(
            TransientState.EIA,
            strategy_name,
            is_write=False,
            lease_valid=lease_valid,
            ops_remaining=ops_remaining,
        )
        is expected
    )
