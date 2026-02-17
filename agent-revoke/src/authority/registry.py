from collections import deque
from typing import Optional, List, Set, Dict
from uuid import UUID

from core.types import Capability, MESIState, CapabilityExhaustedError


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[UUID, Capability] = {}
        self._delegation_tree: Dict[UUID, List[UUID]] = {}
        self._agent_capabilities: Dict[UUID, Set[UUID]] = {}

    def store(self, cap: Capability) -> None:
        self._capabilities[cap.id] = cap
        if cap.agent_id not in self._agent_capabilities:
            self._agent_capabilities[cap.agent_id] = set()
        self._agent_capabilities[cap.agent_id].add(cap.id)

        if cap.parent_cap_id:
            if cap.parent_cap_id not in self._delegation_tree:
                self._delegation_tree[cap.parent_cap_id] = []
            self._delegation_tree[cap.parent_cap_id].append(cap.id)

    def get(self, cap_id: UUID) -> Optional[Capability]:
        return self._capabilities.get(cap_id)

    def get_for_agent(self, agent_id: UUID) -> List[Capability]:
        cap_ids = self._agent_capabilities.get(agent_id, set())
        return [self.get(cap_id) for cap_id in cap_ids if self.get(cap_id) is not None]

    def get_children(self, cap_id: UUID) -> List[Capability]:
        child_ids = self._delegation_tree.get(cap_id, [])
        return [self.get(child_id) for child_id in child_ids if self.get(child_id) is not None]

    def get_all_descendants(self, cap_id: UUID) -> List[Capability]:
        descendants = []
        queue = deque([cap_id])
        visited = {cap_id}

        while queue:
            current_cap_id = queue.popleft()
            children = self.get_children(current_cap_id)
            for child in children:
                if child.id not in visited:
                    descendants.append(child)
                    visited.add(child.id)
                    queue.append(child.id)
        return descendants

    def update_state(self, cap_id: UUID, new_state: MESIState) -> Capability:
        cap = self.get(cap_id)
        if not cap:
            raise ValueError(f"Capability {cap_id} not found")

        new_cap = Capability(**{**cap.__dict__, "state": new_state})
        self.store(new_cap)
        return new_cap

    def increment_ops(self, cap_id: UUID) -> Capability:
        cap = self.get(cap_id)
        if not cap:
            raise ValueError(f"Capability {cap_id} not found")

        if cap.max_operations is not None:
            if cap.operations_used >= cap.max_operations:
                raise CapabilityExhaustedError(cap_id, cap.max_operations)
            new_ops = cap.operations_used + 1
            new_cap = Capability(**{**cap.__dict__, "operations_used": new_ops})
            self.store(new_cap)
            return new_cap
        return cap
