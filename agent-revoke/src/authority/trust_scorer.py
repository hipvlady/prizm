# Copyright (c) 2026 Prizm contributors.
"""Behavioural trust scoring and anomaly detection."""

from __future__ import annotations

from typing import Dict, List
from uuid import UUID

from src.core.types import ActionRecord, ActionResult

ANOMALY_THRESHOLD = 0.3


class TrustScorer:
    """Simple trust scorer used for anomaly-triggered auto-revocation."""

    def __init__(self):
        self._scores: Dict[UUID, float] = {}

    def evaluate(self, agent_id: UUID, action_history: List[ActionRecord]) -> float:
        """Evaluate trust score from recent action outcomes."""
        score = 1.0
        # Use a bounded recent window to support adaptive strategy recovery.
        for action in action_history[-50:]:
            if action.result.value.startswith("denied"):
                score -= 0.1
            elif action.result == ActionResult.EXHAUSTED:
                score -= 0.05
        self._scores[agent_id] = max(0.0, score)
        return self._scores[agent_id]

    def check_anomaly(self, agent_id: UUID, action_history: List[ActionRecord]) -> bool:
        """Detect anomalous action sequences."""
        if len(action_history) > 50:
            recent_actions = action_history[-50:]
            first_tick = recent_actions[0].tick
            last_tick = recent_actions[-1].tick
            if last_tick - first_tick < 10:
                return True

        denied_count = 0
        for action in action_history[-10:]:
            if action.result.value.startswith("denied"):
                denied_count += 1
        return denied_count > 5

    def get_score(self, agent_id: UUID) -> float:
        """Return most recently computed score for agent."""
        return self._scores.get(agent_id, 1.0)
