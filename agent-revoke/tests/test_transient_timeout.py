from __future__ import annotations

from collections import deque
from uuid import uuid4

from src.agent.runtime import AgentRuntime
from src.authority.broadcaster import RevocationBroadcaster
from src.authority.registry import CapabilityRegistry
from src.authority.service import AuthorityService
from src.authority.trust_scorer import TrustScorer
from src.core.clock import LogicalClock
from src.core.mesi import MESIState, TransientState
from src.core.types import Capability
from src.strategies.eager import EagerInvalidationStrategy


def test_lost_ack_times_out_to_invalid():
    clock = LogicalClock()
    authority = AuthorityService(
        CapabilityRegistry(),
        RevocationBroadcaster(deque(), 1, clock),
        TrustScorer(),
        clock,
    )
    agent = AgentRuntime(
        agent_id=uuid4(),
        authority=authority,
        strategy=EagerInvalidationStrategy(),
        clock=clock,
        transient_timeout_ticks=3,
    )
    cap = Capability(
        agent_id=agent.agent_id,
        resource="resource:read",
        state=MESIState.EXCLUSIVE,
        granted_tick=0,
        transient_state=TransientState.EIA,
        transient_entered_tick=0,
    )
    agent.cache.update(cap)

    timed_out = agent.check_transient_timeouts(4)
    assert cap.id in timed_out
    assert agent.cache.get(cap.id).state == MESIState.INVALID
