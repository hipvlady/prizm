import pytest
from src.uuid import uuid4

from src.core.clock import LogicalClock
from src.core.types import (
    MESIState,
    RevocationEvent,
    RevocationReason,
    ActionResult,
    Capability,
)
from src.agent.cache import CapabilityCache
from src.agent.runtime import AgentRuntime
from src.authority.service import AuthorityService
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer

@pytest.fixture
def authority_components():
    clock = LogicalClock()
    registry = CapabilityRegistry()
    broadcaster = RevocationBroadcaster()
    trust_scorer = TrustScorer()
    return clock, registry, broadcaster, trust_scorer

@pytest.fixture
def authority(authority_components):
    clock, registry, broadcaster, trust_scorer = authority_components
    return AuthorityService(registry, broadcaster, trust_scorer, clock)

@pytest.fixture
def agent_runtime(authority):
    agent_id = uuid4()
    cache = CapabilityCache()
    return AgentRuntime(agent_id, authority, cache, authority.clock)

def test_attempt_action_allowed(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=agent_runtime.clock.now(),
        max_operations=10,
    )
    agent_runtime.cache.store(cap)
    
    result = agent_runtime.attempt_action("resource:read")
    assert result == ActionResult.ALLOWED

def test_attempt_action_denied_invalid(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.INVALID,
        granted_at=agent_runtime.clock.now(),
    )
    agent_runtime.cache.store(cap)
    
    result = agent_runtime.attempt_action("resource:read")
    assert result == ActionResult.DENIED

def test_attempt_action_ttl_expired(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=0,
        expires_at=10,
    )
    agent_runtime.cache.store(cap)
    agent_runtime.clock.tick = 11
    
    result = agent_runtime.attempt_action("resource:read")
    assert result == ActionResult.DENIED
    assert agent_runtime.cache.get(cap.id).state == MESIState.INVALID

def test_attempt_action_exhausted(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=agent_runtime.clock.now(),
        max_operations=5,
        operations_used=5,
    )
    agent_runtime.cache.store(cap)
    
    result = agent_runtime.attempt_action("resource:read")
    assert result == ActionResult.EXHAUSTED

def test_attempt_action_unbounded(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=agent_runtime.clock.now(),
        max_operations=None,
    )
    agent_runtime.cache.store(cap)
    
    for _ in range(100):
        result = agent_runtime.attempt_action("resource:read")
        assert result == ActionResult.ALLOWED

def test_on_revocation_invalidates(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=agent_runtime.clock.now(),
    )
    agent_runtime.cache.store(cap)
    
    event = RevocationEvent(
        id=uuid4(),
        capability_id=cap.id,
        reason=RevocationReason.EXPLICIT,
        issued_at=agent_runtime.clock.now(),
    )
    
    agent_runtime.on_revocation(event)
    
    assert agent_runtime.cache.get(cap.id).state == MESIState.INVALID

def test_on_revocation_idempotent(agent_runtime: AgentRuntime):
    cap_id = uuid4()
    event = RevocationEvent(
        id=uuid4(),
        capability_id=cap_id,
        reason=RevocationReason.EXPLICIT,
        issued_at=agent_runtime.clock.now(),
    )
    
    assert agent_runtime.on_revocation(event)
    assert agent_runtime.on_revocation(event)

def test_attempt_write_action_transitions_to_modified(agent_runtime: AgentRuntime):
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_at=agent_runtime.clock.now(),
    )
    agent_runtime.cache.store(cap)
    
    result = agent_runtime.attempt_write_action("resource:read")
    assert result == ActionResult.ALLOWED
    assert agent_runtime.cache.get(cap.id).state == MESIState.MODIFIED

def test_transient_cleanup(agent_runtime: AgentRuntime):
    from src.core.mesi import TransientCapability, TransientState
    cap = Capability(
        id=uuid4(),
        agent_id=agent_runtime.agent_id,
        resource="resource:read",
        state=MESIState.SHARED,
        granted_at=0,
    )
    agent_runtime.cache.store(cap)
    
    transient = TransientCapability(
        capability_id=cap.id,
        from_state=MESIState.SHARED,
        to_state=MESIState.INVALID,
        waiting_for="ACK",
        transient_state=TransientState.SIA,
        tick_entered=0,
        timeout_ticks=100,
    )
    agent_runtime.cache._transients[cap.id] = transient
    
    agent_runtime.clock.tick = 101
    
    resolved_ids = agent_runtime.cache.cleanup_transients(agent_runtime.clock.now())
    
    assert cap.id in resolved_ids
    assert agent_runtime.cache.get(cap.id).state == MESIState.INVALID
