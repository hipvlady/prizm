import pytest
from uuid import uuid4
from collections import deque

from src.core.clock import LogicalClock
from src.core.mesi import MESIState
from src.core.types import RevocationReason, ScopeAttenuationError, ActionRecord, ActionResult
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer
from src.authority.service import AuthorityService

@pytest.fixture
def authority_components():
    """Provides a set of authority components for testing."""
    registry = CapabilityRegistry()
    message_bus = deque()
    clock = LogicalClock()
    broadcaster = RevocationBroadcaster(message_bus, latency_ticks=1, clock=clock)
    trust_scorer = TrustScorer()
    authority = AuthorityService(registry, broadcaster, trust_scorer, clock)
    return authority, registry, message_bus, clock, trust_scorer

def test_grant_and_get_capability(authority_components):
    """Tests that a capability can be granted and retrieved."""
    authority, registry, _, _, _ = authority_components
    agent_id = uuid4()
    
    cap = authority.grant_capability(agent_id=agent_id, resource="test:resource", scope=["read"])
    
    retrieved_cap = registry.get(cap.id)
    assert retrieved_cap is not None
    assert retrieved_cap.agent_id == agent_id
    assert retrieved_cap.resource == "test:resource"

def test_delegation_and_cascade_revocation(authority_components):
    """Tests capability delegation and cascading revocation."""
    authority, registry, message_bus, clock, _ = authority_components
    user_a = uuid4()
    user_b = uuid4()
    user_c = uuid4()

    # 1. Grant root capability to User A
    cap_a = authority.grant_capability(agent_id=user_a, resource="root", scope=["read", "write"])
    
    # 2. Delegate from A to B
    clock.advance()
    cap_b = authority.delegate_capability(
        from_agent_id=user_a,
        to_agent_id=user_b,
        parent_cap_id=cap_a.id,
        attenuated_scope=["read"]
    )
    
    # 3. Delegate from B to C
    clock.advance()
    cap_c = authority.delegate_capability(
        from_agent_id=user_b,
        to_agent_id=user_c,
        parent_cap_id=cap_b.id,
        attenuated_scope=["read"]
    )

    # 4. Verify delegation chain in registry
    chain = registry.get_delegation_chain(cap_a.id)
    assert len(chain) == 2
    assert cap_b in chain
    assert cap_c in chain

    # 5. Revoke root capability with cascade
    clock.advance()
    authority.revoke_capability(capability_id=cap_a.id, reason=RevocationReason.EXPLICIT, cascade=True)

    # 6. Check the message bus for revocation events
    assert len(message_bus) == 3  # A, B, and C should be notified
    notified_agents = {msg['recipient'] for msg in message_bus}
    assert notified_agents == {user_a, user_b, user_c}
    
    # Test non-cascade revocation
    message_bus.clear()
    authority.revoke_capability(capability_id=cap_a.id, reason=RevocationReason.EXPLICIT, cascade=False)
    assert len(message_bus) == 1
    assert message_bus[0]['recipient'] == user_a


def test_delegation_scope_attenuation_error(authority_components):
    """Tests that delegating with a broader scope raises an error."""
    authority, _, _, clock, _ = authority_components
    user_a = uuid4()
    user_b = uuid4()

    cap_a = authority.grant_capability(agent_id=user_a, resource="root", scope=["read"])
    
    clock.advance()
    with pytest.raises(ScopeAttenuationError):
        authority.delegate_capability(
            from_agent_id=user_a,
            to_agent_id=user_b,
            parent_cap_id=cap_a.id,
            attenuated_scope=["read", "write"] # This scope is broader than parent's
        )

def test_trust_scorer_anomaly_detection(authority_components):
    """Tests the TrustScorer's ability to detect anomalous behavior."""
    _, _, _, clock, trust_scorer = authority_components
    agent_id = uuid4()

    # 1. Test bulk operations anomaly
    action_history_bulk = []
    for i in range(60):
        tick = i // 12  # 60 actions within 5 ticks
        action_history_bulk.append(ActionRecord(
            agent_id=agent_id, capability_id=uuid4(), resource="test", tick=tick,
            authorized=True, result=ActionResult.ALLOWED, delegation_depth=0
        ))
    assert trust_scorer.check_anomaly(agent_id, action_history_bulk) is True

    # 2. Test normal activity
    action_history_normal = []
    for i in range(20):
        tick = i * 2  # Actions are spread out
        action_history_normal.append(ActionRecord(
            agent_id=agent_id, capability_id=uuid4(), resource="test", tick=tick,
            authorized=True, result=ActionResult.ALLOWED, delegation_depth=0
        ))
    assert trust_scorer.check_anomaly(agent_id, action_history_normal) is False

    # 3. Test repeated denials anomaly
    action_history_denials = []
    for i in range(10):
        result = ActionResult.DENIED_SCOPE if i < 6 else ActionResult.ALLOWED
        action_history_denials.append(ActionRecord(
            agent_id=agent_id, capability_id=uuid4(), resource="test", tick=i,
            authorized=False, result=result, delegation_depth=0
        ))
    assert trust_scorer.check_anomaly(agent_id, action_history_denials) is True


def test_revoke_enforces_swmr_for_agent_resource(authority_components):
    """Revoking one capability invalidates sibling lines for the same agent/resource pair."""
    authority, registry, message_bus, clock, _ = authority_components
    agent_id = uuid4()

    first = authority.grant_capability(agent_id=agent_id, resource="shared:record", scope=["read"])
    clock.advance()
    sibling = authority.grant_capability(agent_id=agent_id, resource="shared:record", scope=["read"])

    event = authority.revoke_capability(first.id, RevocationReason.EXPLICIT, cascade=False)

    refreshed_first = registry.get(first.id)
    refreshed_sibling = registry.get(sibling.id)
    assert refreshed_first is not None
    assert refreshed_sibling is not None
    assert refreshed_first.state == MESIState.INVALID
    assert refreshed_sibling.state == MESIState.INVALID
    assert event.expected_capabilities == {first.id, sibling.id}
    assert len(message_bus) == 1
    assert message_bus[0]["recipient"] == agent_id
