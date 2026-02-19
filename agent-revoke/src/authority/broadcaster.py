# Copyright (c) 2026 Prizm contributors.
"""Revocation broadcaster for simulated event delivery."""

from __future__ import annotations

from collections import deque
import random
from typing import List
from uuid import UUID

from src.core.clock import LogicalClock
from src.core.types import RevocationEvent
from src.simulation.metrics import MetricsCollector


class RevocationBroadcaster:
    """Broadcast revocation events onto the simulated message bus."""

    def __init__(
        self,
        message_bus: deque,
        latency_ticks: int,
        clock: LogicalClock,
        metrics_collector: MetricsCollector | None = None,
        message_loss_rate: float = 0.0,
        rng: random.Random | None = None,
    ):
        self.message_bus = message_bus
        self.latency_ticks = latency_ticks
        self.clock = clock
        self.metrics_collector = metrics_collector
        self.message_loss_rate = message_loss_rate
        self.rng = rng if rng is not None else random.Random()

    def broadcast(self, event: RevocationEvent, agent_ids: List[UUID]) -> None:
        """Broadcast revocation event to recipients.

        Parameters
        ----------
        event : RevocationEvent
            Revocation event payload.
        agent_ids : list[UUID]
            Recipient agent identifiers.
        """
        if self.metrics_collector is not None:
            self.metrics_collector.record_message_broadcast(len(agent_ids))
        for agent_id in agent_ids:
            if self.message_loss_rate > 0.0 and self.rng.random() < self.message_loss_rate:
                continue
            self.message_bus.append(
                {
                    "recipient": agent_id,
                    "event": event,
                    "deliver_at": self.clock.now() + self.latency_ticks,
                }
            )
