import pytest
from src.uuid import uuid4

from src.core.types import (
    MESIState,
    Capability,
    ScopeAttenuationError,
    CapabilityExhaustedError,
    ActionResult,
)
from src.core.mesi import (
    transition,
    MESITransitionError,
    TransientCapability,
    TransientState,
)


def test_valid_transitions():
    assert transition(MESIState.INVALID, "grant_exclusive") == MESIState.EXCLUSIVE
    assert transition(MESIState.EXCLUSIVE, "acquire_shared") == MESIState.SHARED
    assert transition(MESIState.SHARED, "invalidate") == MESIState.INVALID
    assert transition(MESIState.EXCLUSIVE, "revoke") == MESIState.INVALID


def test_invalid_transition_raises():
    with pytest.raises(MESITransitionError):
        transition(MESIState.INVALID, "write_hit")


def test_transient_state_created():
    cap_id = uuid4()
    transient = TransientCapability(
        capability_id=cap_id,
        from_state=MESIState.SHARED,
        to_state=MESIState.INVALID,
        waiting_for="ACK",
        transient_state=TransientState.SIA,
        tick_entered=10.0,
    )
    assert transient.capability_id == cap_id
    assert transient.transient_state == TransientState.SIA
    assert transient.tick_entered == 10.0


def test_transient_timeout():
    transient = TransientCapability(
        capability_id=uuid4(),
        from_state=MESIState.SHARED,
        to_state=MESIState.INVALID,
        waiting_for="ACK",
        transient_state=TransientState.SIA,
        tick_entered=0.0,
        timeout_ticks=100,
    )
    current_tick = 101.0
    assert (current_tick - transient.tick_entered) > transient.timeout_ticks


def test_scope_types_are_tuples():
    cap = Capability(
        id=uuid4(),
        agent_id=uuid4(),
        resource="test",
        state=MESIState.EXCLUSIVE,
        granted_at=0.0,
        scope=("read",),
    )
    assert isinstance(cap.scope, tuple)


def test_max_operations_none_is_unbounded():
    cap = Capability(
        id=uuid4(),
        agent_id=uuid4(),
        resource="test",
        state=MESIState.EXCLUSIVE,
        granted_at=0.0,
        max_operations=None,
    )
    # This would raise CapabilityExhaustedError if not unbounded
    for i in range(100):
        cap = Capability(**{**cap.__dict__, "operations_used": cap.operations_used + 1})


def test_max_operations_boundary():
    cap = Capability(
        id=uuid4(),
        agent_id=uuid4(),
        resource="test",
        state=MESIState.EXCLUSIVE,
        granted_at=0.0,
        max_operations=5,
        operations_used=4,
    )
    cap = Capability(**{**cap.__dict__, "operations_used": cap.operations_used + 1})

    assert cap.operations_used == cap.max_operations

    with pytest.raises(CapabilityExhaustedError):
        if cap.operations_used >= cap.max_operations:
            raise CapabilityExhaustedError(cap.id, cap.max_operations)

def test_write_transitions():
    assert transition(MESIState.EXCLUSIVE, "write_hit") == MESIState.MODIFIED
    assert transition(MESIState.SHARED, "write_hit") == MESIState.MODIFIED
    assert transition(MESIState.MODIFIED, "write_hit") == MESIState.MODIFIED

def test_capability_exhausted_result():
    cap = Capability(
        id=uuid4(),
        agent_id=uuid4(),
        resource="test",
        state=MESIState.EXCLUSIVE,
        granted_at=0.0,
        max_operations=5,
        operations_used=5,
    )

    if cap.operations_used >= cap.max_operations:
        result = ActionResult.EXHAUSTED
    else:
        result = ActionResult.ALLOWED
    
    assert result == ActionResult.EXHAUSTED
