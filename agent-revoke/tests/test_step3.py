import pytest
from uuid import uuid4
from collections import deque

from src.core.clock import LogicalClock
from src.core.types import (
    MESIState,
    RevocationEvent,
    RevocationReason,
    ActionResult,
    Capability,
)
from src.agent.runtime import AgentRuntime
from src.authority.service import AuthorityService
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer
from src.strategies.eager import EagerInvalidationStrategy

@pytest.fixture
def clock():
    return LogicalClock()

@pytest.fixture
def authority(clock):
    registry = CapabilityRegistry()
    broadcaster = RevocationBroadcaster(deque(), 1, clock)
    trust_scorer = TrustScorer()
    return AuthorityService(registry, broadcaster, trust_scorer, clock)

@pytest.fixture
def strategy():
    return EagerInvalidationStrategy()

@pytest.fixture
def agent_runtime(authority, strategy, clock):
    agent_id = uuid4()
    return AgentRuntime(agent_id, authority, strategy, clock, 5)

def test_attempt_action_allowed(agent_runtime: AgentRuntime):
    cap = Capability(
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=agent_runtime.clock.now(),
        max_operations=10,
    )
    agent_runtime.state.capabilities[cap.id] = cap
    
    record = agent_runtime.attempt_action("resource:read", agent_runtime.clock.now())
    assert record.authorized

def test_attempt_action_denied_invalid(agent_runtime: AgentRuntime):
    cap = Capability(
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.INVALID,
        granted_tick=agent_runtime.clock.now(),
    )
    agent_runtime.state.capabilities[cap.id] = cap
    
    record = agent_runtime.attempt_action("resource:read", agent_runtime.clock.now())
    assert not record.authorized

def test_on_revocation_invalidates(agent_runtime: AgentRuntime):
    cap = Capability(
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=agent_runtime.clock.now(),
    )
    agent_runtime.state.capabilities[cap.id] = cap
    
    event = RevocationEvent(
        capability_id=cap.id,
        reason=RevocationReason.EXPLICIT,
        issued_tick=agent_runtime.clock.now(),
    )
    
    agent_runtime.on_revocation_received(event)
    
    assert agent_runtime.state.capabilities[cap.id].state == MESIState.INVALID