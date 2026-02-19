from types import SimpleNamespace
from uuid import uuid4

from src.authority.registry import CapabilityRegistry
from src.core.mesi import MESIState
from src.core.types import Capability
from src.simulation.consistency import ConsistencyMonitor


def test_check_staleness_tracks_max_window():
    monitor = ConsistencyMonitor()
    registry = CapabilityRegistry()

    agent_id = uuid4()
    cap = Capability(
        id=uuid4(),
        agent_id=agent_id,
        resource="resource:read",
        state=MESIState.INVALID,
        granted_tick=0,
    )
    registry.store(cap)

    # Agent still has stale local view (valid while authority already invalid).
    stale_local = Capability(**{**cap.to_dict(), "state": MESIState.EXCLUSIVE})
    fake_agent = SimpleNamespace(state=SimpleNamespace(capabilities={cap.id: stale_local}))
    agents = {agent_id: fake_agent}

    monitor.check_staleness(agents, tick=5, registry=registry)
    monitor.check_staleness(agents, tick=8, registry=registry)

    # Resolve stale state in agent cache.
    fake_agent.state.capabilities[cap.id] = cap
    monitor.check_staleness(agents, tick=10, registry=registry)

    assert monitor.get_staleness_window_max() == 5
