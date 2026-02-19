# Copyright (c) 2026 Prizm contributors.
"""Network latency simulator utilities."""

from __future__ import annotations

import heapq
from typing import Callable, List, Tuple


class SimulatedNetwork:
    """Inject configurable latency (in ticks) into callback delivery."""

    def __init__(self, latency_ticks: int):
        self.latency_ticks = latency_ticks
        self._queue: List[Tuple[int, Callable]] = []

    def send(self, deliver_at_tick: int, callback: Callable) -> None:
        """Queue a callback for delivery at a given tick."""
        heapq.heappush(self._queue, (deliver_at_tick, callback))

    def process(self, current_tick: int) -> int:
        """Process callbacks due by the current tick.

        Returns
        -------
        int
            Number of callbacks processed.
        """
        count = 0
        while self._queue and self._queue[0][0] <= current_tick:
            _, callback = heapq.heappop(self._queue)
            callback()
            count += 1
        return count
