# Copyright (c) 2026 Prizm contributors.
"""Domain exception hierarchy for agent-revoke."""

from __future__ import annotations

from uuid import UUID


class AgentRevokeError(Exception):
    """Base class for domain errors in the simulation."""


class InvalidTransitionError(AgentRevokeError):
    """Raised when MESI transition table rejects a state transition."""

    def __init__(self, from_state: str, to_state: str, trigger: str):
        super().__init__(
            f"invalid_transition from={from_state} to={to_state} trigger={trigger}"
        )
        self.from_state = from_state
        self.to_state = to_state
        self.trigger = trigger


class ScopeViolationError(AgentRevokeError):
    """Raised when delegated scope is not a subset of parent scope."""

    def __init__(
        self,
        parent_scope: tuple[str, ...],
        child_scope: tuple[str, ...],
    ):
        super().__init__(
            f"child scope {child_scope} must be subset of parent scope {parent_scope}"
        )
        self.parent_scope = parent_scope
        self.child_scope = child_scope


class BudgetExceededError(AgentRevokeError):
    """Raised when delegated operation budget exceeds parent remaining budget."""

    def __init__(self, parent_remaining: int, requested: int, detail: str | None = None):
        message = (
            f"requested budget {requested} exceeds parent remaining budget {parent_remaining}"
        )
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)
        self.parent_remaining = parent_remaining
        self.requested = requested


class DepthExceededError(AgentRevokeError):
    """Raised when delegation depth exceeds configured maximum."""

    def __init__(self, current_depth: int, max_depth: int):
        super().__init__(f"delegation depth {current_depth} exceeds max depth {max_depth}")
        self.current_depth = current_depth
        self.max_depth = max_depth


class CapabilityNotFoundError(AgentRevokeError):
    """Raised when capability identifier is not found in registry."""

    def __init__(self, capability_id: UUID):
        super().__init__(f"capability={capability_id}: not found")
        self.capability_id = capability_id


class AgentNotFoundError(AgentRevokeError):
    """Raised when agent identifier is not found in simulation runtime."""

    def __init__(self, agent_id: UUID):
        super().__init__(f"agent={agent_id}: not found")
        self.agent_id = agent_id


class RevocationError(AgentRevokeError):
    """Raised when a revocation operation cannot be completed."""

    def __init__(self, capability_id: UUID, message: str):
        super().__init__(f"capability={capability_id}: {message}")
        self.capability_id = capability_id


class StaleCredentialError(AgentRevokeError):
    """Raised when an action uses a credential revoked at authority."""

    def __init__(self, agent_id: UUID, capability_id: UUID, message: str):
        super().__init__(f"agent={agent_id} capability={capability_id}: {message}")
        self.agent_id = agent_id
        self.capability_id = capability_id


class CacheMissError(AgentRevokeError):
    """Raised when an agent cannot find a capability for a resource in local cache."""

    def __init__(self, agent_id: UUID, resource: str):
        super().__init__(f"agent={agent_id} resource={resource}: cache miss")
        self.agent_id = agent_id
        self.resource = resource


class DelegationDepthExceededError(AgentRevokeError):
    """Backward-compatible alias for spec-aligned ``DepthExceededError``."""

    def __init__(self, parent_capability_id: UUID, parent_depth: int, max_depth: int):
        super().__init__(f"parent_capability={parent_capability_id}")
        self.parent_capability_id = parent_capability_id
        self.parent_depth = parent_depth
        self.max_depth = max_depth


class RemainingOpsPropagationError(AgentRevokeError):
    """Backward-compatible alias for spec-aligned ``BudgetExceededError``."""

    def __init__(self, parent_capability_id: UUID, message: str):
        super().__init__(f"parent_capability={parent_capability_id}: {message}")
        self.parent_capability_id = parent_capability_id


class ScenarioValidationError(AgentRevokeError):
    """Raised when scenario YAML does not match expected schema."""

    def __init__(self, path: str, message: str):
        super().__init__(f"scenario={path}: {message}")
        self.path = path


# Backward-compatible aliases for pre-spec naming.
DelegationDepthExceededError = DepthExceededError
RemainingOpsPropagationError = BudgetExceededError
