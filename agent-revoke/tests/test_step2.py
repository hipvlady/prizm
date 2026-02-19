import pytest
from uuid import uuid4, UUID
from collections import deque
from src.core.clock import LogicalClock
from src.core.types import (
    MESIState,
    RevocationReason,
    ScopeAttenuationError,
    ActionRecord,
    ActionResult,
    RevocationEvent,
    Capability,
    DelegationPolicy,
)
from src.core.exceptions import DelegationDepthExceededError, RemainingOpsPropagationError
from src.authority.registry import CapabilityRegistry
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.trust_scorer import TrustScorer
from src.authority.service import AuthorityService

@pytest.fixture
def authority_components():
    clock = LogicalClock()
    registry = CapabilityRegistry()
    message_bus = deque()
    broadcaster = RevocationBroadcaster(message_bus, 1, clock)
    trust_scorer = TrustScorer()
    return clock, registry, broadcaster, trust_scorer, message_bus

@pytest.fixture
def authority(authority_components):
    clock, registry, broadcaster, trust_scorer, _ = authority_components
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

def test_revoke_sends_event(authority_components):
    clock, registry, broadcaster, trust_scorer, message_bus = authority_components
    authority = AuthorityService(registry, broadcaster, trust_scorer, clock)
    agent_id = uuid4()
    cap = authority.grant_capability(agent_id, "resource:read")
    
    authority.revoke_capability(cap.id, RevocationReason.EXPLICIT)
    
    assert len(message_bus) == 1
    msg = message_bus[0]
    assert msg["recipient"] == agent_id
    assert msg["event"].capability_id == cap.id

def test_cascade_revoke_sends_multiple_events(authority_components):
    clock, registry, broadcaster, trust_scorer, message_bus = authority_components
    authority = AuthorityService(registry, broadcaster, trust_scorer, clock)
    a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
    cap_a = authority.grant_capability(a, "resource", scope=["read", "write"])
    cap_b = authority.delegate_capability(a, b, cap_a.id, ["read"])
    cap_c = authority.delegate_capability(b, c, cap_b.id, ["read"])
    cap_d = authority.delegate_capability(c, d, cap_c.id, ["read"])

    authority.revoke_capability(cap_a.id, RevocationReason.EXPLICIT, cascade=True)

    assert len(message_bus) == 4
    recipients = {msg["recipient"] for msg in message_bus}
    assert recipients == {a, b, c, d}


def test_delegate_allows_exact_max_depth(authority: AuthorityService):
    authority.set_delegation_policy(DelegationPolicy(max_depth=2))
    a, b, c = uuid4(), uuid4(), uuid4()
    root = authority.grant_capability(a, "resource", scope=["read", "write"])
    child = authority.delegate_capability(a, b, root.id, ["read"])
    grandchild = authority.delegate_capability(b, c, child.id, ["read"])
    assert grandchild.delegation_depth == 2


def test_delegate_rejects_depth_overflow(authority: AuthorityService):
    authority.set_delegation_policy(DelegationPolicy(max_depth=1))
    a, b, c = uuid4(), uuid4(), uuid4()
    root = authority.grant_capability(a, "resource", scope=["read", "write"])
    child = authority.delegate_capability(a, b, root.id, ["read"])
    with pytest.raises(DelegationDepthExceededError):
        authority.delegate_capability(b, c, child.id, ["read"])


def test_delegate_propagates_remaining_ops_exact(authority: AuthorityService):
    authority.set_delegation_policy(DelegationPolicy(max_depth=3, propagate_remaining_ops=True))
    a, b = uuid4(), uuid4()
    parent = authority.grant_capability(
        a, "resource", scope=["read", "write"], max_operations=10
    )
    parent_data = parent.to_dict()
    parent_data["operations_used"] = 4
    authority.registry.update(Capability(**parent_data))

    child = authority.delegate_capability(a, b, parent.id, ["read"])
    assert child.max_operations == 6


def test_delegate_rejects_exhausted_parent_ops(authority: AuthorityService):
    authority.set_delegation_policy(DelegationPolicy(max_depth=3, propagate_remaining_ops=True))
    a, b = uuid4(), uuid4()
    parent = authority.grant_capability(
        a, "resource", scope=["read", "write"], max_operations=5
    )
    parent_data = parent.to_dict()
    parent_data["operations_used"] = 5
    authority.registry.update(Capability(**parent_data))

    with pytest.raises(RemainingOpsPropagationError):
        authority.delegate_capability(a, b, parent.id, ["read"])


@pytest.mark.parametrize("chain_depth", [1, 2, 3, 4])
def test_cascade_expected_capabilities_matches_chain_depth(authority_components, chain_depth: int):
    clock, registry, broadcaster, trust_scorer, message_bus = authority_components
    authority = AuthorityService(registry, broadcaster, trust_scorer, clock)
    authority.set_delegation_policy(DelegationPolicy(max_depth=8))
    agents = [uuid4() for _ in range(chain_depth)]

    root = authority.grant_capability(agents[0], "resource", scope=["read", "write"])
    parent_agent = agents[0]
    parent_cap = root
    for i in range(1, chain_depth):
        child = authority.delegate_capability(parent_agent, agents[i], parent_cap.id, ["read"])
        parent_agent = agents[i]
        parent_cap = child

    event = authority.revoke_capability(root.id, RevocationReason.EXPLICIT, cascade=True)
    assert len(event.expected_capabilities) == chain_depth
    assert len(message_bus) == chain_depth
