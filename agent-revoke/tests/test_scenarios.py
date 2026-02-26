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
