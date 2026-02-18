from typing import Dict, List, Optional
from uuid import UUID

from core.types import RevocationEvent


class RevocationBroadcaster:
    def __init__(self):
        self._pending: Dict[UUID, Dict[UUID, Optional[float]]] = {}

    def broadcast(self, event: RevocationEvent, agent_ids: List[UUID]) -> None:
        if event.id not in self._pending:
            self._pending[event.id] = {agent_id: None for agent_id in agent_ids}

    def record_ack(self, event_id: UUID, agent_id: UUID, tick: float) -> None:
        if event_id in self._pending and agent_id in self._pending[event_id]:
            self._pending[event_id][agent_id] = tick

    def is_fully_propagated(self, event_id: UUID) -> bool:
        if event_id not in self._pending:
            return True
        return all(ack_time is not None for ack_time in self._pending[event_id].values())

    def get_pending_agents(self, event_id: UUID) -> List[UUID]:
        if event_id not in self._pending:
            return []
        return [agent_id for agent_id, ack_time in self._pending[event_id].items() if ack_time is None]

    def get_propagation_status(self, event_id: UUID) -> Dict:
        return self._pending.get(event_id, {})
