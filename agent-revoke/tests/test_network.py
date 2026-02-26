from __future__ import annotations

import random
from uuid import uuid4

from src.simulation.network import Network


def test_network_deliver_due_and_pending_count():
    rng = random.Random(42)
    network = Network(latency_ticks=3, message_loss_rate=0.0, rng=rng)
    dst = uuid4()
    msg = network.send("payload", None, dst, current_tick=5, message_type="revocation")
    assert msg is not None
    assert network.pending_count == 1
    assert network.message_overhead == 1

    assert network.deliver_due(7) == []
    delivered = network.deliver_due(8)
    assert len(delivered) == 1
    assert delivered[0].destination == dst
    assert network.pending_count == 0


def test_network_message_loss():
    rng = random.Random(1)
    network = Network(latency_ticks=1, message_loss_rate=1.0, rng=rng)
    dropped = network.send("payload", None, uuid4(), current_tick=0, message_type="revocation")
    assert dropped is None
    assert network.pending_count == 0
    assert network.message_overhead == 1
