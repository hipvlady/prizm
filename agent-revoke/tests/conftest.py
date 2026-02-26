from __future__ import annotations

from collections import deque
from pathlib import Path
from uuid import uuid4

import pytest

from src.agent.runtime import AgentRuntime
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.registry import CapabilityRegistry
from src.authority.service import AuthorityService
from src.authority.trust_scorer import TrustScorer
from src.core.clock import LogicalClock
from src.core.types import Capability
from src.strategies.eager import EagerInvalidationStrategy


@pytest.fixture(scope="module")
def scenarios_path() -> Path:
    return Path(__file__).parent.parent / "scenarios"


@pytest.fixture(scope="module")
def templates_path() -> Path:
    return Path(__file__).parent.parent / "src" / "output" / "templates"


@pytest.fixture
def authority() -> AuthorityService:
    clock = LogicalClock()
    registry = CapabilityRegistry()
    broadcaster = RevocationBroadcaster(deque(), 1, clock)
    trust_scorer = TrustScorer()
    return AuthorityService(registry, broadcaster, trust_scorer, clock)


@pytest.fixture
def root_agent(authority: AuthorityService) -> tuple[AgentRuntime, Capability]:
    strategy = EagerInvalidationStrategy()
    agent = AgentRuntime(uuid4(), authority, strategy, authority.clock, transient_timeout_ticks=10)
    cap = authority.grant_capability(
        agent_id=agent.agent_id,
        resource="resource:read_write",
        max_operations=100,
        scope=["read", "write"],
    )
    agent.cache.update(cap)
    return agent, cap


@pytest.fixture
def delegation_chain(authority: AuthorityService) -> tuple[list[AgentRuntime], list[Capability]]:
    strategy = EagerInvalidationStrategy()
    a = AgentRuntime(uuid4(), authority, strategy, authority.clock, transient_timeout_ticks=10)
    b = AgentRuntime(uuid4(), authority, strategy, authority.clock, transient_timeout_ticks=10)
    c = AgentRuntime(uuid4(), authority, strategy, authority.clock, transient_timeout_ticks=10)

    cap_a = authority.grant_capability(
        agent_id=a.agent_id,
        resource="resource:read_write",
        scope=["read", "write"],
    )
    cap_b = authority.delegate_capability(a.agent_id, b.agent_id, cap_a.id, ["read"])
    cap_c = authority.delegate_capability(b.agent_id, c.agent_id, cap_b.id, ["read"])

    a.cache.update(cap_a)
    b.cache.update(cap_b)
    c.cache.update(cap_c)
    return [a, b, c], [cap_a, cap_b, cap_c]
