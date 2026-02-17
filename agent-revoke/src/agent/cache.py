from typing import Dict, Optional, List
from uuid import UUID

from core.types import Capability, MESIState, ActionResult, CapabilityExhaustedError
from core.mesi import TransientCapability


class CapabilityCache:
    """Local MESI cache at the PEP (AgentRuntime). NOT canonical state."""

    def __init__(self):
        self._cache: Dict[UUID, Capability] = {}
        self._transients: Dict[UUID, TransientCapability] = {}

    def get(self, cap_id: UUID) -> Optional[Capability]:
        return self._cache.get(cap_id)

    def store(self, cap: Capability) -> None:
        self._cache[cap.id] = cap

    def invalidate(self, cap_id: UUID) -> None:
        cap = self.get(cap_id)
        if cap:
            new_cap = Capability(**{**cap.__dict__, "state": MESIState.INVALID})
            self.store(new_cap)

    def expire_ttl(self, cap_id: UUID, current_tick: float) -> bool:
        cap = self.get(cap_id)
        if cap and cap.expires_at is not None and current_tick >= cap.expires_at:
            self.invalidate(cap_id)
            return True
        return False

    def check_exec_count(self, cap_id: UUID) -> ActionResult:
        cap = self.get(cap_id)
        if cap:
            if cap.max_operations is not None and cap.operations_used >= cap.max_operations:
                return ActionResult.EXHAUSTED
        return ActionResult.ALLOWED

    def increment_ops(self, cap_id: UUID) -> None:
        cap = self.get(cap_id)
        if cap:
            if cap.max_operations is not None and cap.operations_used >= cap.max_operations:
                raise CapabilityExhaustedError(cap.id, cap.max_operations)
            
            new_ops = cap.operations_used + 1
            new_cap = Capability(**{**cap.__dict__, "operations_used": new_ops})
            self.store(new_cap)

    def update_state(self, cap_id: UUID, new_state: MESIState) -> None:
        cap = self.get(cap_id)
        if cap:
            new_cap = Capability(**{**cap.__dict__, "state": new_state})
            self.store(new_cap)

    def get_by_resource(self, resource: str) -> Optional[Capability]:
        for cap in self._cache.values():
            if cap.resource == resource:
                return cap
        return None

    def cleanup_transients(self, current_tick: float, timeout_ticks: int = 100) -> List[UUID]:
        resolved_ids = []
        for cap_id, transient in list(self._transients.items()):
            if current_tick - transient.tick_entered >= timeout_ticks:
                self.invalidate(cap_id)
                resolved_ids.append(cap_id)
                del self._transients[cap_id]
        return resolved_ids
