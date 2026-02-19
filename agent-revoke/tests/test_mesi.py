import pytest
from src.core.mesi import MESIState, is_valid_transition

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
