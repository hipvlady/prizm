from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
from uuid import UUID

from from core.types import RevocationEvent, ActionResult, Capability
from from authority.service import AuthorityService
from from agent.runtime import AgentRuntime


@dataclass
class StrategyResult:
    strategy: str
    propagation_complete: bool
    agents_notified: int
    agents_acked: int
    ticks_elapsed: int
    unauthorized_ops_during_propagation: int  # KEY METRIC


class RevocationStrategy(ABC):
    name: str
    coherence_class: str  # "consistency-agnostic" or "consistency-directed"

    @abstractmethod
    def on_revocation_issued(
        self,
        event: RevocationEvent,
        authority: AuthorityService,
        agents: Dict[UUID, AgentRuntime],
    ) -> StrategyResult:
        ...

    @abstractmethod
    def on_action_attempt(
        self,
        agent: AgentRuntime,
        resource: str,
        capability: Capability,
    ) -> ActionResult:
        ...

    @abstractmethod
    def get_staleness_bound(self) -> str:
        """Human-readable bound: '60s TTL', 'N=50 ops', 'network_latency', 'check_interval'"""
