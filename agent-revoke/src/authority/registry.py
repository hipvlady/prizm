# Copyright (c) 2026 Prizm contributors.
"""Authority capability registry with delegation graph traversal."""

from __future__ import annotations

import collections
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.core.mesi import MESIState
from src.core.types import Capability, DelegationEdge


class CapabilityRegistry:
    """Canonical in-memory capability registry."""

    def __init__(self):
        self._capabilities: Dict[UUID, Capability] = {}
        self._delegation_tree: Dict[UUID, Set[UUID]] = collections.defaultdict(set)

    def store(self, cap: Capability):
        """Store capability and update delegation tree if required."""
        self._capabilities[cap.id] = cap
        if cap.parent_cap_id:
            self._delegation_tree[cap.parent_cap_id].add(cap.id)

    def get(self, capability_id: UUID) -> Optional[Capability]:
        """Fetch capability by identifier."""
        return self._capabilities.get(capability_id)

    def find_by_agent_resource(self, agent_id: UUID, resource: str) -> Optional[Capability]:
        """Find first valid capability by agent and resource."""
        for cap in self._capabilities.values():
            if cap.agent_id == agent_id and cap.resource == resource and cap.state != MESIState.INVALID:
                return cap
        return None

    def list_by_agent_resource(self, agent_id: UUID, resource: str) -> List[Capability]:
        """List all capabilities for one agent/resource pair."""
        return [
            cap
            for cap in self._capabilities.values()
            if cap.agent_id == agent_id and cap.resource == resource
        ]

    def update(self, capability: Capability):
        """Update existing capability record."""
        if capability.id not in self._capabilities:
            raise ValueError(f"Capability {capability.id} not found in registry.")
        self._capabilities[capability.id] = capability

    def get_delegation_chain(self, capability_id: UUID) -> List[Capability]:
        """Return BFS traversal of descendants from root capability.

        Parameters
        ----------
        capability_id : UUID
            Root capability identifier.

        Returns
        -------
        list[Capability]
            Descendant capabilities in breadth-first order.
        """
        chain = []
        queue = collections.deque([capability_id])
        visited = {capability_id}

        while queue:
            current_id = queue.popleft()
            cap = self.get(current_id)
            if not cap:
                continue

            for child_id in self._delegation_tree.get(current_id, []):
                if child_id not in visited:
                    child_cap = self.get(child_id)
                    if child_cap:
                        chain.append(child_cap)
                        visited.add(child_id)
                        queue.append(child_id)
        return chain

    def get_delegation_tree_snapshot(self) -> Dict[str, List[str]]:
        """Return delegation graph snapshot (parent capability -> child capabilities)."""
        snapshot: Dict[str, List[str]] = {}
        for parent, children in self._delegation_tree.items():
            snapshot[str(parent)] = [str(child) for child in sorted(children, key=str)]
        return snapshot

    def get_delegation_edges(self) -> List[DelegationEdge]:
        """Return explicit delegation edges with capability/agent metadata."""
        edges: List[DelegationEdge] = []
        for parent_id, children in self._delegation_tree.items():
            parent = self.get(parent_id)
            if parent is None:
                continue
            for child_id in sorted(children, key=str):
                child = self.get(child_id)
                if child is None:
                    continue
                edges.append(
                    DelegationEdge(
                        parent_cap_id=parent_id,
                        child_cap_id=child_id,
                        parent_agent_id=parent.agent_id,
                        child_agent_id=child.agent_id,
                        depth=child.delegation_depth,
                        attenuated_scope=child.scope,
                    )
                )
        return edges
