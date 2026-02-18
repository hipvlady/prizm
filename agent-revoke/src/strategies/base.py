from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.runtime import AgentRuntime
    from src.core.types import Capability, RevocationEvent, ActionRecord


class CoherenceClass(Enum):
    CONSISTENCY_AGNOSTIC = "consistency-agnostic"   # Primer Ch.2 §2.3
    CONSISTENCY_DIRECTED = "consistency-directed"


class BoundType(Enum):
    TIME = "time"
    OPERATIONS = "operations"
    HYBRID = "hybrid"


class ActionResult(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING_VALIDATION = "pending_validation"
    EXHAUSTED = "exhausted"       # max_operations reached (RCC release)
    EXPIRED = "expired"           # TTL elapsed (temporal coherence self-invalidation)
    TIMEOUT = "timeout"           # transient state timed out (ADR-005)


@dataclass
class StrategyMetrics:
    revalidation_count: int = 0
    transient_state_durations: dict[str, float] = dataclasses.field(default_factory=dict)


class RevocationStrategy(ABC):
    name: str
    coherence_class: CoherenceClass
    bound_type: BoundType

    @abstractmethod
    def initiate_revocation(self, event: "RevocationEvent", agents: list["AgentRuntime"]) -> None:
        """Called when authority issues revocation.
        consistency-agnostic: blocks until all agents ACK (SWMR)
        consistency-directed: returns immediately, agents discover asynchronously
        """
        ...

    @abstractmethod
    def validate_action(self, agent: "AgentRuntime", capability: "Capability") -> ActionResult:
        """Called when agent wants to perform action.
        Must handle transient states (Primer Ch.6 §6.4.1): EIA, SIA, MIC
        Must check transient timeout (ADR-005)
        """
        ...

    @abstractmethod
    def on_tick(self, agent: "AgentRuntime", tick: int):
        """Called each simulation tick.
        Resolves transient states, checks lease expiry (temporal coherence).
        Checks transient state timeouts (ADR-005).
        """
        ...

    @abstractmethod
    def record_action(self, agent: "AgentRuntime", capability: "Capability", action: "ActionRecord") -> None:
        """Post-action hook: increment counters, check bounds.
        exec-count: acts as RCC 'release' when max_ops reached (Primer Ch.10 §10.1.4)
        """
        ...

    def revalidate(self, agent: "AgentRuntime", capability: "Capability") -> Optional["Capability"]:
        """RCC-like re-validation: agent requests fresh credentials after exhaustion.
        Acts as RCC 'acquire' — self-invalidate local cache, pull fresh state.
        Returns new Capability or None if denied.
        """
        return None

    @abstractmethod
    def get_metrics(self) -> "StrategyMetrics":
        ...

    @abstractmethod
    def get_theoretical_bound(self) -> str:
        """Human-readable bound description."""
        ...

    @property
    def is_clock_dependent(self) -> bool:
        """Whether this strategy depends on synchronized clocks."""
        return self.bound_type == BoundType.TIME
