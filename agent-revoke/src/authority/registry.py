from __future__ import annotations
import collections
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.core.types import Capability, MESIState


class CapabilityRegistry:
    """
    The Authority's core database (PDP). It stores the canonical state of all capabilities.
    It is the single source of truth. Agent caches are considered secondary.
    This implementation uses a simple in-memory dictionary.
    """
    def __init__(self):
        self._capabilities: Dict[UUID, Capability] = {}
        self._delegation_tree: Dict[UUID, Set[UUID]] = collections.defaultdict(set) # parent_id -> {child_ids}

    def store(self, cap: Capability):
        self._capabilities[cap.id] = cap
        if cap.parent_cap_id:
            self._delegation_tree[cap.parent_cap_id].add(cap.id)

    def get(self, capability_id: UUID) -> Optional[Capability]:
        return self._capabilities.get(capability_id)

    def find_by_agent_resource(self, agent_id: UUID, resource: str) -> Optional[Capability]:
        for cap in self._capabilities.values():
            if cap.agent_id == agent_id and cap.resource == resource and cap.state != MESIState.INVALID:
                return cap
        return None

    def update(self, capability: Capability):
        """Updates a capability state in the registry."""
        if capability.id not in self._capabilities:
            raise ValueError(f"Capability {capability.id} not found in registry.")
        self._capabilities[capability.id] = capability

    def get_delegation_chain(self, capability_id: UUID) -> List[Capability]:
        """Performs a BFS traversal to get all children in a delegation chain (ADR-004)."""
        chain = []
        queue = collections.deque([capability_id])
        visited = {capability_id}
        
        while queue:
            current_id = queue.popleft()
            cap = self.get(current_id)
            if not cap: continue
            
            for child_id in self._delegation_tree.get(current_id, []):
                if child_id not in visited:
                    child_cap = self.get(child_id)
                    if child_cap:
                        chain.append(child_cap)
                        visited.add(child_id)
                        queue.append(child_id)
        return chain