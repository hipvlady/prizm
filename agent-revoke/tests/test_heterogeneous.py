# Copyright (c) 2026 Prizm contributors.
"""Tests for heterogeneous role-based strategy assignment."""

from pathlib import Path

from src.simulation.engine import SimulationEngine
from src.simulation.scenarios import load_scenario
from src.strategies.selector import StrategySelector


SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def test_strategy_selector_policy_and_fallback() -> None:
    selector = StrategySelector(
        {"banking": "eager", "crm": "lease", "analytics": "lazy", "api": "exec_count"}
    )
    assert selector.select("banking") == "eager"
    assert selector.select("api") == "exec_count"
    assert selector.select("unlisted-role") == "lazy"


def test_strategy_selector_ignores_invalid_strategy_mapping() -> None:
    selector = StrategySelector({"api": "unsupported"}, fallback="eager")
    assert selector.select("api") == "eager"


def test_engine_assigns_per_agent_strategies_from_roles() -> None:
    scenario_file = SCENARIOS_DIR / "banking-cascade.yaml"
    config = load_scenario(str(scenario_file))
    config["simulation"]["num_agents"] = 5
    config["simulation"]["agents"] = 5
    config["simulation"]["duration_ticks"] = 1
    config["heterogeneous"] = {
        "enabled": True,
        "policy": {
            "banking": "eager",
            "crm": "lease",
            "analytics": "lazy",
            "api": "exec_count",
        },
        "agent_roles": ["banking", "crm", "analytics", "api", "unknown"],
    }

    engine = SimulationEngine(config, "eager", str(scenario_file))
    strategy_names = [agent.strategy.name for agent in engine.agents.values()]

    assert strategy_names == ["eager", "lease", "lazy", "exec_count", "lazy"]
    assert engine.strategy_name == "heterogeneous"

    metrics = engine.run()
    assert metrics.strategy == "heterogeneous"
