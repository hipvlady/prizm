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
from src.strategies.lease import LeaseBasedStrategy

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
    return LeaseBasedStrategy(default_ttl_ticks=10)

@pytest.fixture
def agent_runtime(authority, strategy, clock):
    agent_id = uuid4()
    return AgentRuntime(agent_id, authority, strategy, clock, 5)

def test_attempt_action_denied_expired(agent_runtime: AgentRuntime):
    cap = Capability(
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=0,
        expires_tick=10,
    )
    agent_runtime.state.capabilities[cap.id] = cap
    agent_runtime.clock.tick = 11
    
    record = agent_runtime.attempt_action("resource:read", agent_runtime.clock.now())
    assert not record.authorized
    assert agent_runtime.state.capabilities[cap.id].state == MESIState.INVALID

def test_on_tick_invalidates_expired(agent_runtime: AgentRuntime):
    cap = Capability(
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=0,
        expires_tick=10,
    )
    agent_runtime.state.capabilities[cap.id] = cap
    agent_runtime.clock.tick = 11
    
    agent_runtime.strategy.on_tick(agent_runtime, agent_runtime.clock.now())
    
    assert agent_runtime.state.capabilities[cap.id].state == MESIState.INVALID