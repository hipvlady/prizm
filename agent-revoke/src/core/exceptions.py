# Copyright (c) 2026 Prizm contributors.
"""Domain exception hierarchy for agent-revoke."""

from __future__ import annotations

from uuid import UUID


class AgentRevokeError(Exception):
    """Base class for domain errors in the simulation."""


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
