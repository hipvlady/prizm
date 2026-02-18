import pytest
from uuid import uuid4

from src.core.types import (
    MESIState,
    Capability,
    ScopeAttenuationError,
    CapabilityExhaustedError,
)

def test_capability_creation():
    agent_id = uuid4()
    cap = Capability(
        agent_id=agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=10,
        scope=("read",),
    )
    assert cap.agent_id == agent_id
    assert cap.resource == "resource:read"
    assert cap.state == MESIState.EXCLUSIVE
    assert cap.granted_tick == 10
    assert cap.scope == ("read",)

def test_capability_to_dict():
    agent_id = uuid4()
    cap = Capability(
        agent_id=agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=10,
        scope=("read",),
    )
    cap_dict = cap.to_dict()
    assert cap_dict["agent_id"] == agent_id
    assert cap_dict["resource"] == "resource:read"
    assert cap_dict["state"] == MESIState.EXCLUSIVE
    assert cap_dict["granted_tick"] == 10
    assert cap_dict["scope"] == ("read",)

def test_scope_attenuation_error():
    with pytest.raises(ScopeAttenuationError):
        raise ScopeAttenuationError(("read", "write"), ("read",))

def test_capability_exhausted_error():
    with pytest.raises(CapabilityExhaustedError):
        raise CapabilityExhaustedError()