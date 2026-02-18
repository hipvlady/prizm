import pytest
from src.uuid import uuid4, UUID
from src.core.clock import LogicalClock
from src.core.types import MESIState, RevocationReason, ScopeAttenuationError, ActionRecord, ActionResult, RevocationEvent
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer
from src.authority.service import AuthorityService

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

def test_grant_creates_exclusive_state(authority: AuthorityService):
    agent_id = uuid4()
    cap = authority.grant_capability(agent_id, "resource:read")
    assert cap.state == MESIState.EXCLUSIVE
    stored_cap = authority.registry.get(cap.id)
    assert stored_cap is not None
    assert stored_cap.state == MESIState.EXCLUSIVE

def test_delegate_with_valid_scope(authority: AuthorityService):
    owner_id = uuid4()
    delegate_id = uuid4()
    parent_cap = authority.grant_capability(owner_id, "resource:read", scope=["read", "write"])
    
    child_cap = authority.delegate_capability(owner_id, delegate_id, parent_cap.id, ["read"])
    
    assert child_cap is not None
    assert set(child_cap.scope) == {"read"}
    assert child_cap.parent_cap_id == parent_cap.id

def test_delegate_with_invalid_scope_raises_error(authority: AuthorityService):
    owner_id = uuid4()
    delegate_id = uuid4()
    parent_cap = authority.grant_capability(owner_id, "resource:read", scope=["read"])
    
    with pytest.raises(ScopeAttenuationError):
        authority.delegate_capability(owner_id, delegate_id, parent_cap.id, ["read", "write"])

def test_delegate_respects_op_count(authority: AuthorityService):
    owner_id = uuid4()
    delegate_id = uuid4()
    parent_cap = authority.grant_capability(owner_id, "resource:read", max_operations=10)
    authority.registry.increment_ops(parent_cap.id) # Use one op
    
    child_cap = authority.delegate_capability(owner_id, delegate_id, parent_cap.id, [])
    
    assert child_cap.max_operations == 9

def test_revoke_changes_state(authority: AuthorityService):
    agent_id = uuid4()
    cap = authority.grant_capability(agent_id, "resource:read")
    
    authority.revoke_capability(cap.id, RevocationReason.EXPLICIT)
    
    revoked_cap = authority.registry.get(cap.id)
    assert revoked_cap is not None
    assert revoked_cap.state == MESIState.INVALID

def test_cascade_revoke_bfs(authority: AuthorityService):
    a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
    cap_a = authority.grant_capability(a, "resource", scope=["read", "write"])
    cap_b = authority.delegate_capability(a, b, cap_a.id, ["read"])
    cap_c = authority.delegate_capability(b, c, cap_b.id, ["read"])
    cap_d = authority.delegate_capability(c, d, cap_c.id, ["read"])

    authority.revoke_capability(cap_a.id, RevocationReason.EXPLICIT, cascade=True)

    assert authority.registry.get(cap_a.id).state == MESIState.INVALID
    assert authority.registry.get(cap_b.id).state == MESIState.INVALID
    assert authority.registry.get(cap_c.id).state == MESIState.INVALID
    assert authority.registry.get(cap_d.id).state == MESIState.INVALID

def test_trust_anomaly_triggers_revoke(authority: AuthorityService):
    agent_id = uuid4()
    cap = authority.grant_capability(agent_id, "resource:read")
    
    action_history = []
    for i in range(6):
        action_history.append(ActionRecord(agent_id=agent_id, resource="resource:read", result=ActionResult.DENIED, tick=i))

    if authority.trust_scorer.check_anomaly(agent_id, action_history):
        authority.revoke_capability(cap.id, RevocationReason.TRUST_VIOLATION)

    revoked_cap = authority.registry.get(cap.id)
    assert revoked_cap is not None
    assert revoked_cap.state == MESIState.INVALID

def test_broadcaster_tracks_acks(authority: AuthorityService):
    agent1, agent2, agent3 = uuid4(), uuid4(), uuid4()
    cap_id = uuid4()
    
    event = RevocationEvent(id=uuid4(), capability_id=cap_id, reason=RevocationReason.EXPLICIT, issued_at=authority.clock.now())
    authority.broadcaster.broadcast(event, [agent1, agent2, agent3])
    
    authority.broadcaster.record_ack(event.id, agent1, authority.clock.now())
    authority.broadcaster.record_ack(event.id, agent2, authority.clock.now())
    
    assert not authority.broadcaster.is_fully_propagated(event.id)
    
    authority.broadcaster.record_ack(event.id, agent3, authority.clock.now())
    
    assert authority.broadcaster.is_fully_propagated(event.id)
