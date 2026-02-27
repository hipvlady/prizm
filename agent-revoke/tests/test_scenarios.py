# Copyright (c) 2026 Prizm contributors.
"""Scenario loading and schema validation tests."""

from pathlib import Path

import pytest
import yaml

from src.core.exceptions import ScenarioValidationError
from src.simulation.scenarios import load_scenario


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_load_valid_scenario_adds_heterogeneous_defaults(tmp_path: Path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    payload = {
        "simulation": {
            "duration_ticks": 10,
            "agents": 2,
            "action_probability": 0.5,
            "latency_ticks": 1,
            "transient_timeout_ticks": 10,
        },
        "scenario": {
            "name": "valid",
            "delegation_depth": 1,
            "cascade_revocation": False,
            "revocation_trigger_tick": 1,
        },
        "strategies": {
            "lazy": {"check_interval_ticks": 2},
            "lease": {"default_ttl_ticks": 10},
            "exec_count": {"max_operations": 3},
        },
        "trust": {
            "initial_score": 0.8,
            "anomaly_threshold": 0.4,
            "score_decay_on_anomaly": 0.3,
        },
        "delegation": {
            "max_depth": 3,
            "require_scope_subset": True,
            "propagate_remaining_ops": True,
        },
    }
    _write_yaml(scenario_path, payload)

    config = load_scenario(str(scenario_path))

    assert "heterogeneous" in config
    assert config["heterogeneous"]["enabled"] is False
    assert "adaptive_strategy" in config
    assert config["adaptive_strategy"]["enabled"] is False


def test_load_scenario_rejects_missing_action_rate(tmp_path: Path) -> None:
    scenario_path = tmp_path / "invalid.yaml"
    payload = {
        "simulation": {
            "duration_ticks": 10,
            "agents": 2,
            "latency_ticks": 1,
            "transient_timeout_ticks": 10,
        },
        "scenario": {
            "name": "invalid",
            "delegation_depth": 1,
            "cascade_revocation": False,
            "revocation_trigger_tick": 1,
        },
        "strategies": {"lazy": {}, "lease": {}, "exec_count": {}},
        "trust": {},
        "delegation": {},
    }
    _write_yaml(scenario_path, payload)

    with pytest.raises(ScenarioValidationError):
        load_scenario(str(scenario_path))


def test_load_scenario_rejects_invalid_heterogeneous_policy(tmp_path: Path) -> None:
    scenario_path = tmp_path / "invalid-hetero.yaml"
    payload = {
        "simulation": {
            "duration_ticks": 10,
            "agents": 2,
            "actions_per_tick": 1,
            "latency_ticks": 1,
            "transient_timeout_ticks": 10,
        },
        "scenario": {
            "name": "invalid-hetero",
            "delegation_depth": 1,
            "cascade_revocation": False,
            "revocation_trigger_tick": 1,
        },
        "strategies": {"lazy": {}, "lease": {}, "exec_count": {}},
        "trust": {},
        "delegation": {},
        "heterogeneous": {
            "enabled": True,
            "policy": {"api": "invalid-strategy"},
            "agent_roles": ["api", "api"],
        },
    }
    _write_yaml(scenario_path, payload)

    with pytest.raises(ScenarioValidationError):
        load_scenario(str(scenario_path))


def test_load_scenario_rejects_invalid_adaptive_strategy(tmp_path: Path) -> None:
    scenario_path = tmp_path / "invalid-adaptive.yaml"
    payload = {
        "simulation": {
            "duration_ticks": 10,
            "agents": 2,
            "actions_per_tick": 1,
            "latency_ticks": 1,
            "transient_timeout_ticks": 10,
        },
        "scenario": {
            "name": "invalid-adaptive",
            "delegation_depth": 1,
            "cascade_revocation": False,
            "revocation_trigger_tick": 1,
        },
        "strategies": {"lazy": {}, "lease": {}, "exec_count": {}},
        "trust": {},
        "delegation": {},
        "adaptive_strategy": {
            "enabled": True,
            "evaluate_interval_ticks": 1,
            "low_trust_threshold": 0.5,
            "recover_trust_threshold": 0.8,
            "high_risk_strategy": "not-a-strategy",
        },
    }
    _write_yaml(scenario_path, payload)

    with pytest.raises(ScenarioValidationError):
        load_scenario(str(scenario_path))


def test_reference_scenarios_match_spec_authoritative_values() -> None:
    base = Path(__file__).resolve().parent.parent / "scenarios"
    banking = load_scenario(str(base / "banking-cascade.yaml"))
    crm = load_scenario(str(base / "crm-bulk-ops.yaml"))
    anomaly = load_scenario(str(base / "anomaly-autorevoke.yaml"))

    assert banking["simulation"]["duration_ticks"] == 300
    assert banking["simulation"]["num_agents"] == 5
    assert banking["network"]["latency_ticks"] == 5
    assert banking["scenario"]["revocation_tick"] == 50
    assert banking["scenario"]["agent_velocity"] == 10
    assert banking["strategies"]["exec_count"]["max_operations"] == 10

    assert crm["simulation"]["duration_ticks"] == 500
    assert crm["simulation"]["num_agents"] == 5
    assert crm["scenario"]["delegation_depth"] == 2
    assert crm["scenario"]["revocation_tick"] == 50
    assert crm["scenario"]["agent_velocity"] == 100
    assert crm["strategies"]["exec_count"]["max_operations"] == 500

    assert anomaly["simulation"]["duration_ticks"] == 300
    assert anomaly["simulation"]["num_agents"] == 5
    assert anomaly["scenario"]["delegation_depth"] == 2
    assert anomaly["scenario"]["anomaly_start_tick"] == 50
    assert anomaly["scenario"]["anomaly_burst_rate"] == 12
    assert anomaly["strategies"]["exec_count"]["max_operations"] == 1000
