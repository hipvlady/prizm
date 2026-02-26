from collections import deque
from uuid import uuid4

from src.agent.runtime import AgentRuntime
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.registry import CapabilityRegistry
from src.authority.service import AuthorityService
from src.authority.trust_scorer import TrustScorer
from src.core.clock import LogicalClock
from src.core.types import RevocationReason
from src.simulation.consistency import ConsistencyMonitor
from src.strategies.lazy import LazyInvalidationStrategy


def test_pull_revocation_has_delivery_and_eventual_completion():
    clock = LogicalClock()
    registry = CapabilityRegistry()
    message_bus = deque()
    monitor = ConsistencyMonitor()
    authority = AuthorityService(
        registry=registry,
        broadcaster=RevocationBroadcaster(message_bus, latency_ticks=1, clock=clock),
        trust_scorer=TrustScorer(),
        clock=clock,
        monitor=monitor,
    )

    agent_id = uuid4()
    strategy = LazyInvalidationStrategy(check_interval_ticks=0)
    agent = AgentRuntime(
        agent_id=agent_id,
        authority=authority,
        strategy=strategy,
        clock=clock,
        transient_timeout_ticks=5,
        monitor=monitor,
    )

    cap = authority.grant_capability(agent_id=agent_id, resource="resource:read", scope=["read"])
    agent.cache.update(cap)

    event = authority.revoke_capability(
        capability_id=cap.id,
        reason=RevocationReason.EXPLICIT,
        cascade=True,
        completion_semantics="pull_eventual",
    )

    msg = message_bus.popleft()
    delivery_tick = msg["deliver_at"]
    agent.on_revocation_received(msg["event"], tick=delivery_tick)

    status_after_delivery = authority.get_revocation_status(event.id)
    assert status_after_delivery["completion_semantics"] == "pull_eventual"
    assert status_after_delivery["pending_acks"] == 0
    assert status_after_delivery["delivery_complete"] is True
    assert status_after_delivery["delivery_completion_tick"] == delivery_tick
    assert status_after_delivery["local_cascade_complete"] is False
    assert status_after_delivery["pending_capabilities"] == 1

    strategy.on_tick(agent, delivery_tick + 1)
    status_after_reconcile = authority.get_revocation_status(event.id)
    assert status_after_reconcile["local_cascade_complete"] is True
    assert status_after_reconcile["cascade_completeness_ratio"] == 1.0
    assert status_after_reconcile["pending_capabilities"] == 0

    trace_events = [entry.event for entry in monitor.get_revocation_trace(event.id)]
    assert "observe_pull" in trace_events
    assert "capability_invalidated" in trace_events
