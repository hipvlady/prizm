# Copyright (c) 2026 Prizm contributors.
"""Logical clock for deterministic simulation ordering."""

from dataclasses import dataclass


@dataclass
class LogicalClock:
    """Monotonic tick clock used by the simulation engine."""

    tick: int = 0

    def advance(self, n: int = 1) -> int:
        """Advance clock by a non-negative number of ticks.

        Parameters
        ----------
        n : int, optional
            Tick increment.

        Returns
        -------
        int
            Current tick after increment.
        """
        if n < 0:
            raise ValueError("Cannot advance clock backwards")
        self.tick += n
        return self.tick

    def now(self) -> int:
        """Return current tick value."""
        return self.tick

    def elapsed_since(self, past_tick: int) -> int:
        """Return elapsed ticks relative to a past tick."""
        if past_tick > self.tick:
            raise ValueError("past_tick cannot be in the future")
        return self.tick - past_tick
