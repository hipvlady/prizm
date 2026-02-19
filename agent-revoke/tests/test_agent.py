import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from src.core.clock import LogicalClock
from src.core.types import Capability, RevocationEvent, RevocationReason
from src.core.mesi import MESIState, TransientState
from src.agent.runtime import AgentRuntime
from src.strategies.base import ActionResult
from src.strategies.exec_count import ExecCountStrategy

@pytest.fixture
def mock_strategy():
    """A mock revocation strategy that allows all actions."""
    strategy = MagicMock()
    strategy.validate_action.return_value = ActionResult.ALLOWED
    return strategy

@pytest.fixture
def agent_runtime(mock_strategy):
    """Provides an AgentRuntime instance with mocked dependencies."""
    runtime = AgentRuntime(
        agent_id=uuid4(),
        authority=MagicMock(),
        strategy=mock_strategy,
        clock=LogicalClock(),
        transient_timeout_ticks=10
    )
    return runtime

def test_transient_state_timeout(agent_runtime):
    """
    Tests that a capability in a transient state for too long is invalidated.
    (ADR-005)
    """
    cap_id = uuid4()
    # Create a capability that has been in a transient state for 15 ticks
    transient_cap = Capability(
        id=cap_id,
        agent_id=agent_runtime.agent_id,
        resource="test",
        state=MESIState.EXCLUSIVE,
        granted_tick=0,
        transient_state=TransientState.EIA,
        transient_entered_tick=0
    )
    agent_runtime.cache.update(transient_cap)
    
    # Advance the clock far enough to trigger the timeout
    current_tick = 15
    agent_runtime.cache.check_transient_timeouts(current_tick)
    
    # Check that the capability is now invalid
    updated_cap = agent_runtime.cache.get(cap_id)
    assert updated_cap is not None
    assert updated_cap.state == MESIState.INVALID

def test_operation_counting():
    """
    Tests that agent actions correctly increment the operations_used counter.
    """
    strategy = ExecCountStrategy()
    agent_runtime = AgentRuntime(
        agent_id=uuid4(),
        authority=MagicMock(),
        strategy=strategy,
        clock=LogicalClock(),
        transient_timeout_ticks=10
    )
    cap_id = uuid4()
    cap = Capability(
        id=cap_id,
        agent_id=agent_runtime.agent_id,
        resource="test_ops",
        state=MESIState.EXCLUSIVE,
        granted_tick=0,
        max_operations=100
    )
    agent_runtime.cache.update(cap)
    
    # Attempt an action
    agent_runtime.attempt_action(resource="test_ops", tick=1)
    
    # Check the counter
    updated_cap = agent_runtime.cache.get(cap_id)
    assert updated_cap.operations_used == 1

def test_revocation_received(agent_runtime):
    """
    Tests that the agent runtime correctly handles a revocation event.
    """
    cap_id = uuid4()
    cap = Capability(
        id=cap_id,
        agent_id=agent_runtime.agent_id,
        resource="test_revocation",
        state=MESIState.SHARED,
        granted_tick=0
    )
    agent_runtime.cache.update(cap)

    # Send a revocation event
    revocation_event = RevocationEvent(
        capability_id=cap_id,
        reason=RevocationReason.EXPLICIT,
        issued_tick=1
    )
    agent_runtime.on_revocation_received(revocation_event)

    # Assert that the cache was updated
    updated_cap = agent_runtime.cache.get(cap_id)
    assert updated_cap.state == MESIState.INVALID
