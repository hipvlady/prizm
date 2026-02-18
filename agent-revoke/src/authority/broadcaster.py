from typing import List
from uuid import UUID
from collections import deque

from src.core.types import RevocationEvent
from src.core.clock import LogicalClock

class RevocationBroadcaster:
    def __init__(self, message_bus: deque, latency_ticks: int, clock: LogicalClock):
        self.message_bus = message_bus
        self.latency_ticks = latency_ticks
        self.clock = clock

    def broadcast(self, event: RevocationEvent, agent_ids: List[UUID]) -> None:
        for agent_id in agent_ids:
            self.message_bus.append({
                "recipient": agent_id,
                "event": event,
                "deliver_at": self.clock.now() + self.latency_ticks,
            })

