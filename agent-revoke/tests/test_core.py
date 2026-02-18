import pytest
from uuid import uuid4

from src.core.clock import LogicalClock
from src.core.mesi import MESIState, is_valid_transition
from src.core.types import Capability

def test_logical_clock_advances():
    """Tests that the logical clock advances monotonically."""
    clock = LogicalClock()
    assert clock.now() == 0
    clock.advance()
    assert clock.now() == 1
    for _ in range(10):
        clock.advance()
    assert clock.now() == 11

def test_capability_creation():
    """Tests basic creation of the Capability dataclass."""
    agent_id = uuid4()
    cap = Capability(
        agent_id=agent_id,
        resource="test:resource",
        state=MESIState.EXCLUSIVE,
        granted_tick=100
    )
    assert cap.agent_id == agent_id
    assert cap.resource == "test:resource"
    assert cap.state == MESIState.EXCLUSIVE
    assert cap.granted_tick == 100
    assert cap.operations_used == 0

@pytest.mark.parametrize("start_state, end_state, expected", [
    (MESIState.INVALID, MESIState.SHARED, True),
    (MESIState.INVALID, MESIState.EXCLUSIVE, True),
    (MESIState.SHARED, MESIState.INVALID, True),
    (MESIState.SHARED, MESIState.EXCLUSIVE, True),
    (MESIState.EXCLUSIVE, MESIState.SHARED, True),
    (MESIState.EXCLUSIVE, MESIState.MODIFIED, True),
    (MESIState.EXCLUSIVE, MESIState.INVALID, True),
    (MESIState.MODIFIED, MESIState.INVALID, True),
    (MESIState.MODIFIED, MESIState.SHARED, True),
    # Invalid transitions
    (MESIState.INVALID, MESIState.MODIFIED, False),
    (MESIState.SHARED, MESIState.MODIFIED, False),
    (MESIState.MODIFIED, MESIState.EXCLUSIVE, False), # Should go through I first
])
def test_mesi_transitions(start_state, end_state, expected):
    """
    Tests the is_valid_transition function with both valid and invalid state transitions
    based on the specification.
    """
    assert is_valid_transition(start_state, end_state) == expected
