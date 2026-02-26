from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from src.agent.runtime import AgentRuntime
from src.core.clock import LogicalClock
from src.core.mesi import MESIState, TransientState
from src.core.types import Capability
from src.strategies.base import ActionResult
from src.strategies.eager import EagerInvalidationStrategy
from src.strategies.exec_count import ExecCountStrategy
from src.strategies.lazy import LazyInvalidationStrategy
from src.strategies.lease import LeaseBasedStrategy


def _agent_with_cap(strategy, *, state=MESIState.EXCLUSIVE, **cap_kwargs):
    authority = MagicMock()
    runtime = AgentRuntime(
        agent_id=uuid4(),
        authority=authority,
        strategy=strategy,
        clock=LogicalClock(),
        transient_timeout_ticks=10,
    )
    cap = Capability(
        agent_id=runtime.agent_id,
        resource="resource:read",
        state=state,
        granted_tick=0,
        **cap_kwargs,
    )
    runtime.cache.update(cap)
    return runtime, cap


def test_eager_blocks_invalidation_transient():
    strategy = EagerInvalidationStrategy()
    agent, cap = _agent_with_cap(
        strategy,
        transient_state=TransientState.EIA,
        transient_entered_tick=0,
    )
    assert strategy.validate_action(agent, cap) == ActionResult.DENIED_TRANSIENT


def test_lazy_allows_during_transient():
    strategy = LazyInvalidationStrategy(check_interval_ticks=100)
    agent, cap = _agent_with_cap(
        strategy,
        transient_state=TransientState.EIA,
        transient_entered_tick=0,
    )
    assert strategy.validate_action(agent, cap) == ActionResult.ALLOWED


def test_lease_self_invalidates_on_expiry():
    strategy = LeaseBasedStrategy(default_ttl_ticks=5)
    agent, cap = _agent_with_cap(strategy, expires_tick=0)
    agent.clock.tick = 1
    result = strategy.validate_action(agent, cap)
    assert result == ActionResult.EXPIRED
    assert agent.cache.get(cap.id).state == MESIState.INVALID


def test_exec_count_exhausts_at_max_operations():
    strategy = ExecCountStrategy(max_operations=3)
    agent, cap = _agent_with_cap(strategy, max_operations=3, operations_used=3)
    result = strategy.validate_action(agent, cap)
    assert result == ActionResult.EXHAUSTED


def test_exec_count_operations_used_monotonic():
    strategy = ExecCountStrategy(max_operations=5)
    agent, cap = _agent_with_cap(strategy, max_operations=5, operations_used=0)
    strategy.record_action(agent, cap, MagicMock())
    first = agent.cache.get(cap.id).operations_used
    strategy.record_action(agent, agent.cache.get(cap.id), MagicMock())
    second = agent.cache.get(cap.id).operations_used
    assert second >= first
