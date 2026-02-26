# Copyright (c) 2026 Prizm contributors.
"""Role-based strategy selection for heterogeneous simulations."""

from __future__ import annotations


class StrategySelector:
    """Select a strategy name for one agent role."""

    _SUPPORTED_STRATEGIES = {"eager", "lazy", "lease", "exec_count"}

    def __init__(self, policy: dict[str, str], fallback: str = "lazy") -> None:
        """Initialise selector with a role->strategy policy mapping."""
        normalized_policy: dict[str, str] = {}
        for role, strategy in policy.items():
            role_key = role.strip().lower()
            strategy_name = strategy.strip()
            if strategy_name in self._SUPPORTED_STRATEGIES and role_key:
                normalized_policy[role_key] = strategy_name
        self._policy = normalized_policy
        self._fallback = fallback if fallback in self._SUPPORTED_STRATEGIES else "lazy"

    def select(self, agent_role: str) -> str:
        """Return strategy name for the supplied role, with fallback."""
        role_key = agent_role.strip().lower()
        return self._policy.get(role_key, self._fallback)
