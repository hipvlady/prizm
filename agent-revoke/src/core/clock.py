from dataclasses import dataclass, field


@dataclass
class LogicalClock:
    tick: int = 0

    def advance(self, n: int = 1) -> int:
        if n < 0:
            raise ValueError("Cannot advance clock backwards")
        self.tick += n
        return self.tick

    def now(self) -> int:
        return self.tick

    def elapsed_since(self, past_tick: int) -> int:
        if past_tick > self.tick:
            raise ValueError("past_tick cannot be in the future")
        return self.tick - past_tick
