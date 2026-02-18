from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.runtime import AgentRuntime
    from core.types import Capability, RevocationEvent

class RevocationStrategy(ABC):
    """
    Abstract Base Class for all revocation strategies.
    Each strategy defines a different coherence protocol for managing capability state between the agent (PEP) and the authority (PDP).
    """

    @abstractmethod
    def on_grant(self, agent: AgentRuntime, capability: Capability) -> Capability:
        """Called when a new capability is granted to the agent."""
        pass

    @abstractmethod
    def on_delegate(self, agent: AgentRuntime, parent_cap: Capability, child_cap: Capability) -> tuple[Capability, Capability]:
        """Called when a capability is delegated from this agent to another."""
        pass

    @abstractmethod
    def on_revoke(self, agent: AgentRuntime, event: RevocationEvent) -> Capability:
        """Called when a revocation event is received for a capability held by the agent."""
        pass

    @abstractmethod
    def on_action(self, agent: AgentRuntime, capability: Capability) -> Capability:
        """Called before an agent attempts to use a capability."""
        pass

    @abstractmethod
    def on_tick(self, agent: AgentRuntime, tick: int):
        """Called on every simulation tick to handle time-based logic (e.g., leases)."""
        pass
