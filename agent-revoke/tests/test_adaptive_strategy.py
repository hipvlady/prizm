# Copyright (c) 2026 Prizm contributors.
"""Tests for trust-driven adaptive strategy switching."""

from pathlib import Path
from uuid import uuid4

from src.core.types import ActionRecord
from src.simulation.engine import SimulationEngine
from src.simulation.scenarios import load_scenario
from src.strategies.base import ActionResult


SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def _record(agent_id, tick: int, result: ActionResult) -> ActionRecord:
    return ActionRecord(
        agent_id=agent_id,
        capability_id=uuid4(),
        resource="resource:read",
        tick=tick,
        authorized=result == ActionResult.ALLOWED,
        result=result,
        delegation_depth=0,
    )


def test_adaptive_strategy_switches_on_low_trust_and_recovers() -> None:
    scenario_file = SCENARIOS_DIR / "crm-bulk-ops.yaml"
    config = load_scenario(str(scenario_file))
    config["simulation"]["num_agents"] = 1
    config["simulation"]["agents"] = 1
    config["simulation"]["duration_ticks"] = 2
    config["scenario"]["delegation_depth"] = 0
    config["adaptive_strategy"] = {
        "enabled": True,
        "evaluate_interval_ticks": 1,
        "low_trust_threshold": 0.8,
        "recover_trust_threshold": 0.95,
        "high_risk_strategy": "eager",
    }

    engine = SimulationEngine(config, "lazy", str(scenario_file))
    agent = next(iter(engine.agents.values()))
    assert agent.strategy.name == "lazy"

    for tick in range(5):
        agent.state.action_history.append(
            _record(agent.agent_id, tick=tick, result=ActionResult.DENIED_SCOPE)
        )
    engine._run_adaptive_strategy(0)

    assert agent.strategy.name == "eager"
    assert engine.agent_strategy_names[agent.agent_id] == "eager"

    agent.state.action_history.clear()
    for tick in range(5, 10):
        agent.state.action_history.append(
            _record(agent.agent_id, tick=tick, result=ActionResult.ALLOWED)
        )
    engine._run_adaptive_strategy(1)

    assert agent.strategy.name == "lazy"
    assert engine.agent_strategy_names[agent.agent_id] == "lazy"
