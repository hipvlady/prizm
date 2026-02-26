# Copyright (c) 2026 Prizm contributors.
"""Simulated network transport with latency and loss."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Optional
from uuid import UUID


@dataclass
class NetworkMessage:
    """Message envelope used by the simulated network."""

    payload: Any
    source: Optional[UUID]
    destination: UUID
    message_type: str
    sent_tick: int
    delivery_tick: int
    delivered: bool = False


class Network:
    """Simulated network with configurable latency and message loss."""

    def __init__(self, latency_ticks: int, message_loss_rate: float, rng: random.Random) -> None:
        self._queue: Deque[NetworkMessage] = deque()
        self._latency = latency_ticks
        self._loss_rate = message_loss_rate
        self._rng = rng
        self._total_sent: int = 0

    def send(
        self,
        payload: Any,
        source: Optional[UUID],
        destination: UUID,
        current_tick: int,
        message_type: str,
    ) -> NetworkMessage | None:
        """Enqueue message for future delivery or drop on simulated loss."""
        self._total_sent += 1
        if self._loss_rate > 0.0 and self._rng.random() < self._loss_rate:
            return None

        msg = NetworkMessage(
            payload=payload,
            source=source,
            destination=destination,
            message_type=message_type,
            sent_tick=current_tick,
            delivery_tick=current_tick + self._latency,
        )
        self._queue.append(msg)
        return msg

    def deliver_due(self, current_tick: int) -> list[NetworkMessage]:
        """Deliver all queued messages scheduled up to ``current_tick``."""
        due: list[NetworkMessage] = []
        remaining: Deque[NetworkMessage] = deque()
        while self._queue:
            msg = self._queue.popleft()
            if msg.delivery_tick <= current_tick:
                msg.delivered = True
                due.append(msg)
            else:
                remaining.append(msg)
        self._queue = remaining
        return due

    @property
    def pending_count(self) -> int:
        """Return queued messages awaiting delivery."""
        return len(self._queue)

    @property
    def message_overhead(self) -> int:
        """Return total attempted sends."""
        return self._total_sent

    @property
    def latency_ticks(self) -> int:
        """Return configured latency in ticks."""
        return self._latency
