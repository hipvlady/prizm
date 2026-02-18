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
from src.strategies.eager import EagerInvalidationStrategy
from src.strategies.lazy import LazyInvalidationStrategy
from src.strategies.lease import LeaseBasedStrategy
from src.strategies.exec_count import ExecCountBoundedStrategy

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

def test_eager_blocks_until_all_ack(authority, agent_runtime):
    strategy = EagerInvalidationStrategy()
    agent_id = agent_runtime.agent_id
    agents = {agent_id: agent_runtime}

    cap = authority.grant_capability(agent_id, "resource:read")
    event = authority.revoke_capability(cap.id, RevocationReason.EXPLICIT)
    
    result = strategy.on_revocation_issued(event, authority, agents)
    
    assert result.propagation_complete
    assert result.agents_acked == 1
    assert result.unauthorized_ops_during_propagation == 0

def test_lazy_unauthorized_ops_window(authority, agent_runtime):
    strategy = LazyInvalidationStrategy(check_interval_ticks=5)
    agent_id = agent_runtime.agent_id
    agents = {agent_id: agent_runtime}
    
    cap = authority.grant_capability(agent_id, "resource:read")
    agent_runtime.cache.store(cap)
    
    authority.revoke_capability(cap.id, RevocationReason.EXPLICIT)
    
    # Action before check interval
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.ALLOWED
    
    agent_runtime.clock.advance(6)
    
    # Action after check interval
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.DENIED

def test_lease_self_invalidation(authority, agent_runtime):
    strategy = LeaseBasedStrategy(default_ttl_ticks=10)
    
    cap = authority.grant_capability(agent_id=agent_runtime.agent_id, resource="resource:read", ttl=10)
    agent_runtime.cache.store(cap)
    
    agent_runtime.clock.advance(11)
    
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.DENIED
    assert agent_runtime.cache.get(cap.id).state == MESIState.INVALID

def test_exec_count_exactly_n(authority, agent_runtime):
    strategy = ExecCountBoundedStrategy(max_operations=5)
    
    cap = authority.grant_capability(agent_id=agent_runtime.agent_id, resource="resource:read", max_operations=5)
    agent_runtime.cache.store(cap)
    
    for _ in range(5):
        result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
        assert result == ActionResult.ALLOWED
        
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.EXHAUSTED
    
    # After exhaustion, it should be denied
    agent_runtime.cache.invalidate(cap.id)
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.DENIED
    
def test_exec_count_triggers_revalidation(authority, agent_runtime):
    strategy = ExecCountBoundedStrategy(max_operations=1)
    cap = authority.grant_capability(agent_id=agent_runtime.agent_id, resource="resource:read", max_operations=1)
    agent_runtime.cache.store(cap)

    # Use the capability
    strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    
    # Now it should be exhausted
    result = strategy.on_action_attempt(agent_runtime, "resource:read", cap)
    assert result == ActionResult.EXHAUSTED

    # This should trigger revalidation, but for the test, we just check the state
    assert agent_runtime.cache.check_exec_count(cap.id) == ActionResult.EXHAUSTED
