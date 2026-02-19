# Copyright (c) 2026 Prizm contributors.
"""Base strategy interfaces for revocation coherence policies."""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import ActionRecord, Capability, RevocationEvent


class CoherenceClass(Enum):
    """Coherence class from consistency taxonomy."""

    CONSISTENCY_AGNOSTIC = "consistency-agnostic"
    CONSISTENCY_DIRECTED = "consistency-directed"


class BoundType(Enum):
    """Primary staleness bound axis."""

    TIME = "time"
    OPERATIONS = "operations"
    HYBRID = "hybrid"


class ActionResult(Enum):
    """Action validation outcomes."""

    ALLOWED = "allowed"
    DENIED_INVALID = "denied_invalid"
    DENIED_TRANSIENT = "denied_transient"
    DENIED_SCOPE = "denied_scope"
    DENIED_GENERIC = "denied"
    PENDING_VALIDATION = "pending_validation"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    TIMEOUT = "timeout"


@dataclass
class StrategyMetrics:
    """Strategy-local metrics snapshot."""

    revalidation_count: int = 0
    transient_state_durations: dict[str, float] = dataclasses.field(default_factory=dict)


class RevocationStrategy(ABC):
    """Abstract base class for all revocation strategies."""

    name: str
    coherence_class: CoherenceClass
    bound_type: BoundType

    @abstractmethod
    def initiate_revocation(self, event: "RevocationEvent", agents: list["AgentRuntime"]) -> None:
        """Handle authority-side revocation initiation."""

    @abstractmethod
    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """Validate one action attempt against strategy rules."""

    @abstractmethod
    def on_tick(self, agent: "AgentRuntime", tick: int):
        """Run periodic strategy logic for one tick."""

    @abstractmethod
    def record_action(
        self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord"
    ) -> None:
        """Record post-action effects (for example operation counters)."""

    def revalidate(self, agent: "AgentRuntime", capability: "Capability") -> Optional["Capability"]:
        """Attempt strategy-specific capability revalidation."""
        return None

    @abstractmethod
    def get_metrics(self) -> "StrategyMetrics":
        """Return strategy-local metrics."""

    @abstractmethod
    def get_theoretical_bound(self) -> str:
        """Return human-readable staleness bound description."""

    @abstractmethod
    def get_transient_state_duration(self) -> dict[str, float]:
        """Return observed transient-state durations."""

    @property
    def is_clock_dependent(self) -> bool:
        """Return whether strategy depends on synchronised clocks."""
        return self.bound_type == BoundType.TIME

    @property
    def accepts_push_revocation(self) -> bool:
        """Return whether push revocation must invalidate local cache immediately."""
        return self.coherence_class == CoherenceClass.CONSISTENCY_AGNOSTIC
