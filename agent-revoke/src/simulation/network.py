from typing import List, Tuple, Callable
import heapq

class SimulatedNetwork:
    """Inject configurable latency (in ticks) into message delivery."""

    def __init__(self, latency_ticks: int):
        self.latency_ticks = latency_ticks
        self._queue: List[Tuple[int, Callable]] = []

    def send(self, deliver_at_tick: int, callback: Callable) -> None:
        heapq.heappush(self._queue, (deliver_at_tick, callback))

    def process(self, current_tick: int) -> int:
        count = 0
        while self._queue and self._queue[0][0] <= current_tick:
            _, callback = heapq.heappop(self._queue)
            callback()
            count += 1
        return count
