"""Scenario loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from src.core.exceptions import ScenarioValidationError
from src.core.logging_utils import get_logger

LOGGER = get_logger(__name__)

_SUPPORTED_STRATEGIES = {"eager", "lazy", "lease", "exec_count"}


def _require_mapping(data: Any, path: Path, field: str) -> Dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise ScenarioValidationError(str(path), f"'{field}' must be a mapping")
    return value


def _require_int(
    value: Any,
    *,
    path: Path,
    field: str,
    min_value: int | None = None,
    allow_none: bool = False,
) -> int | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, int):
        raise ScenarioValidationError(str(path), f"'{field}' must be an integer")
    if min_value is not None and value < min_value:
        raise ScenarioValidationError(str(path), f"'{field}' must be >= {min_value}")
    return value


def _require_float(
    value: Any,
    *,
    path: Path,
    field: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if not isinstance(value, (int, float)):
        raise ScenarioValidationError(str(path), f"'{field}' must be numeric")
    result = float(value)
    if min_value is not None and result < min_value:
        raise ScenarioValidationError(str(path), f"'{field}' must be >= {min_value}")
    if max_value is not None and result > max_value:
        raise ScenarioValidationError(str(path), f"'{field}' must be <= {max_value}")
    return result


def _require_bool(value: Any, *, path: Path, field: str) -> bool:
    if not isinstance(value, bool):
        raise ScenarioValidationError(str(path), f"'{field}' must be boolean")
    return value


def _normalize_legacy_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    simulation = data.setdefault("simulation", {})
    scenario = data.setdefault("scenario", {})
    if "adaptive_strategy" not in data and "adaptive" in data:
        data["adaptive_strategy"] = data["adaptive"]

    if "num_agents" not in simulation and "agents" in simulation:
        simulation["num_agents"] = simulation["agents"]
    if "seed" not in simulation:
        simulation["seed"] = 42

    if "network" not in data:
        data["network"] = {
            "latency_ticks": simulation.get("latency_ticks", 1),
            "message_loss_rate": simulation.get("message_loss_rate", 0.0),
        }
    else:
        network = data["network"]
        if "latency_ticks" not in network and "latency_ticks" in simulation:
            network["latency_ticks"] = simulation["latency_ticks"]
        if "message_loss_rate" not in network and "message_loss_rate" in simulation:
            network["message_loss_rate"] = simulation["message_loss_rate"]

    if "transient" not in data:
        data["transient"] = {"timeout_ticks": simulation.get("transient_timeout_ticks", 5)}
    elif "timeout_ticks" not in data["transient"] and "transient_timeout_ticks" in simulation:
        data["transient"]["timeout_ticks"] = simulation["transient_timeout_ticks"]

    if "revocation_tick" not in scenario and "revocation_trigger_tick" in scenario:
        scenario["revocation_tick"] = scenario["revocation_trigger_tick"]
    if "cascade_on_revoke" not in scenario and "cascade_revocation" in scenario:
        scenario["cascade_on_revoke"] = scenario["cascade_revocation"]
    if "anomaly_start_tick" not in scenario and "anomaly_behavior_starts_tick" in scenario:
        scenario["anomaly_start_tick"] = scenario["anomaly_behavior_starts_tick"]
    if "anomaly_burst_rate" not in scenario and "anomaly_burst_actions_per_tick" in scenario:
        scenario["anomaly_burst_rate"] = scenario["anomaly_burst_actions_per_tick"]

    if "agent_velocity" not in scenario and "actions_per_tick" in simulation:
        scenario["agent_velocity"] = simulation["actions_per_tick"]
    scenario.setdefault("agent_velocity", 1)
    if "action_probability" not in scenario and "action_probability" in simulation:
        scenario["action_probability"] = simulation["action_probability"]
    if "action_probability" not in scenario:
        scenario["action_probability"] = 1.0 if "agent_velocity" in scenario else 0.0
    scenario.setdefault("anomaly_start_tick", None)
    scenario.setdefault("anomaly_burst_rate", None)
    scenario.setdefault("anomaly_detection_window", None)

    return data


def _validate_simulation(simulation: Dict[str, Any], path: Path) -> None:
    _require_int(
        simulation.get("duration_ticks"),
        path=path,
        field="simulation.duration_ticks",
        min_value=1,
    )
    _require_int(
        simulation.get("num_agents"),
        path=path,
        field="simulation.num_agents",
        min_value=1,
    )
    _require_int(simulation.get("seed"), path=path, field="simulation.seed")


def _validate_network(network: Dict[str, Any], path: Path) -> None:
    _require_int(
        network.get("latency_ticks"),
        path=path,
        field="network.latency_ticks",
        min_value=0,
    )
    _require_float(
        network.get("message_loss_rate"),
        path=path,
        field="network.message_loss_rate",
        min_value=0.0,
        max_value=0.999999,
    )


def _validate_transient(transient: Dict[str, Any], path: Path) -> None:
    _require_int(
        transient.get("timeout_ticks"),
        path=path,
        field="transient.timeout_ticks",
        min_value=1,
    )


def _validate_scenario_block(scenario: Dict[str, Any], simulation: Dict[str, Any], path: Path) -> None:
    name = scenario.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ScenarioValidationError(str(path), "'scenario.name' must be a non-empty string")
    _require_int(
        scenario.get("delegation_depth"),
        path=path,
        field="scenario.delegation_depth",
        min_value=0,
    )
    _require_bool(
        scenario.get("cascade_on_revoke"),
        path=path,
        field="scenario.cascade_on_revoke",
    )
    revocation_tick = _require_int(
        scenario.get("revocation_tick"),
        path=path,
        field="scenario.revocation_tick",
        min_value=0,
        allow_none=True,
    )
    if revocation_tick is not None and revocation_tick >= int(simulation["duration_ticks"]):
        raise ScenarioValidationError(
            str(path),
            "'scenario.revocation_tick' must be < simulation.duration_ticks",
        )
    if int(scenario["delegation_depth"]) >= int(simulation["num_agents"]):
        raise ScenarioValidationError(
            str(path),
            "'scenario.delegation_depth' must be < simulation.num_agents",
        )

    _require_float(
        scenario.get("action_probability"),
        path=path,
        field="scenario.action_probability",
        min_value=0.0,
        max_value=1.0,
    )
    _require_int(
        scenario.get("agent_velocity", 1),
        path=path,
        field="scenario.agent_velocity",
        min_value=1,
    )
    _require_int(
        scenario.get("anomaly_start_tick"),
        path=path,
        field="scenario.anomaly_start_tick",
        min_value=0,
        allow_none=True,
    )
    _require_int(
        scenario.get("anomaly_burst_rate"),
        path=path,
        field="scenario.anomaly_burst_rate",
        min_value=0,
        allow_none=True,
    )
    _require_int(
        scenario.get("anomaly_detection_window"),
        path=path,
        field="scenario.anomaly_detection_window",
        min_value=1,
        allow_none=True,
    )


def _validate_strategies(strategies: Dict[str, Any], path: Path) -> None:
    for key in ("eager", "lazy", "lease", "exec_count"):
        if key not in strategies:
            continue
        if not isinstance(strategies[key], dict):
            raise ScenarioValidationError(str(path), f"'strategies.{key}' must be a mapping")
    _require_int(
        strategies.get("lazy", {}).get("check_interval_ticks", 100),
        path=path,
        field="strategies.lazy.check_interval_ticks",
        min_value=1,
    )
    _require_int(
        strategies.get("lease", {}).get("default_ttl_ticks", 500),
        path=path,
        field="strategies.lease.default_ttl_ticks",
        min_value=1,
    )
    _require_int(
        strategies.get("exec_count", {}).get("max_operations", 50),
        path=path,
        field="strategies.exec_count.max_operations",
        min_value=1,
    )


def _validate_trust(trust: Dict[str, Any], path: Path) -> None:
    for field in ("initial_score", "anomaly_threshold", "score_decay_on_anomaly"):
        if field not in trust:
            continue
        _require_float(
            trust[field],
            path=path,
            field=f"trust.{field}",
            min_value=0.0,
            max_value=1.0,
        )


def _validate_delegation(delegation: Dict[str, Any], path: Path) -> None:
    if "max_depth" in delegation:
        _require_int(
            delegation.get("max_depth"),
            path=path,
            field="delegation.max_depth",
            min_value=1,
        )
    for key in ("require_scope_subset", "propagate_remaining_ops"):
        if key in delegation:
            _require_bool(delegation.get(key), path=path, field=f"delegation.{key}")


def _validate_heterogeneous(heterogeneous: Dict[str, Any], path: Path) -> None:
    enabled = heterogeneous.get("enabled", False)
    _require_bool(enabled, path=path, field="heterogeneous.enabled")
    policy = heterogeneous.get("policy", {})
    if not isinstance(policy, dict):
        raise ScenarioValidationError(str(path), "'heterogeneous.policy' must be a mapping")
    for role, strategy in policy.items():
        if not isinstance(role, str) or not role.strip():
            raise ScenarioValidationError(
                str(path),
                "'heterogeneous.policy' role keys must be non-empty strings",
            )
        if strategy not in _SUPPORTED_STRATEGIES:
            raise ScenarioValidationError(
                str(path),
                "'heterogeneous.policy' strategy values must be one of: eager, lazy, lease, exec_count",
            )
    agent_roles = heterogeneous.get("agent_roles", [])
    if not isinstance(agent_roles, list) or not all(isinstance(x, str) for x in agent_roles):
        raise ScenarioValidationError(str(path), "'heterogeneous.agent_roles' must be a list of strings")


def _validate_adaptive_strategy(adaptive: Dict[str, Any], path: Path) -> None:
    _require_bool(adaptive.get("enabled", False), path=path, field="adaptive_strategy.enabled")
    _require_int(
        adaptive.get("evaluate_interval_ticks", 1),
        path=path,
        field="adaptive_strategy.evaluate_interval_ticks",
        min_value=1,
    )
    _require_float(
        adaptive.get("low_trust_threshold", 0.5),
        path=path,
        field="adaptive_strategy.low_trust_threshold",
        min_value=0.0,
        max_value=1.0,
    )
    recover = adaptive.get("recover_trust_threshold", 0.8)
    _require_float(
        recover,
        path=path,
        field="adaptive_strategy.recover_trust_threshold",
        min_value=0.0,
        max_value=1.0,
    )
    if float(recover) < float(adaptive.get("low_trust_threshold", 0.5)):
        raise ScenarioValidationError(
            str(path),
            "'adaptive_strategy.recover_trust_threshold' must be >= low_trust_threshold",
        )
    strategy = adaptive.get("high_risk_strategy", "eager")
    if strategy not in _SUPPORTED_STRATEGIES:
        raise ScenarioValidationError(
            str(path),
            "'adaptive_strategy.high_risk_strategy' must be one of: eager, lazy, lease, exec_count",
        )


def _populate_runtime_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
    """Backfill legacy aliases while keeping spec-canonical keys present."""
    simulation = data["simulation"]
    network = data["network"]
    scenario = data["scenario"]
    transient = data["transient"]

    simulation["agents"] = simulation["num_agents"]
    simulation["latency_ticks"] = network["latency_ticks"]
    simulation["message_loss_rate"] = network["message_loss_rate"]
    simulation["transient_timeout_ticks"] = transient["timeout_ticks"]
    simulation["action_probability"] = scenario["action_probability"]
    simulation["actions_per_tick"] = scenario["agent_velocity"]

    scenario["revocation_trigger_tick"] = scenario["revocation_tick"]
    scenario["cascade_revocation"] = scenario["cascade_on_revoke"]
    scenario["anomaly_behavior_starts_tick"] = scenario.get("anomaly_start_tick")
    scenario["anomaly_burst_actions_per_tick"] = scenario.get("anomaly_burst_rate")
    return data


def validate_scenario(data: Dict[str, Any], scenario_path: str | Path) -> Dict[str, Any]:
    """Validate scenario payload and return normalized config."""
    path = Path(scenario_path)
    if not isinstance(data, dict):
        raise ScenarioValidationError(str(path), "scenario YAML root must be a mapping")
    provided_rate = False
    if isinstance(data.get("simulation"), dict):
        provided_rate = provided_rate or (
            "action_probability" in data["simulation"] or "actions_per_tick" in data["simulation"]
        )
    if isinstance(data.get("scenario"), dict):
        provided_rate = provided_rate or (
            "action_probability" in data["scenario"] or "agent_velocity" in data["scenario"]
        )
    if not provided_rate:
        raise ScenarioValidationError(
            str(path),
            "scenario must define either action probability or agent velocity",
        )

    normalized = _normalize_legacy_keys(data)
    simulation = _require_mapping(normalized, path, "simulation")
    network = _require_mapping(normalized, path, "network")
    scenario = _require_mapping(normalized, path, "scenario")
    strategies = _require_mapping(normalized, path, "strategies")
    trust = _require_mapping(normalized, path, "trust")
    delegation = _require_mapping(normalized, path, "delegation")
    transient = _require_mapping(normalized, path, "transient")

    _validate_simulation(simulation, path)
    _validate_network(network, path)
    _validate_transient(transient, path)
    _validate_scenario_block(scenario, simulation, path)
    _validate_strategies(strategies, path)
    _validate_trust(trust, path)
    _validate_delegation(delegation, path)
    if "heterogeneous" in normalized:
        if not isinstance(normalized["heterogeneous"], dict):
            raise ScenarioValidationError(str(path), "'heterogeneous' must be a mapping")
        _validate_heterogeneous(normalized["heterogeneous"], path)
    else:
        normalized["heterogeneous"] = {"enabled": False, "policy": {}, "agent_roles": []}

    if "adaptive_strategy" in normalized:
        if not isinstance(normalized["adaptive_strategy"], dict):
            raise ScenarioValidationError(str(path), "'adaptive_strategy' must be a mapping")
        _validate_adaptive_strategy(normalized["adaptive_strategy"], path)
    else:
        normalized["adaptive_strategy"] = {
            "enabled": False,
            "evaluate_interval_ticks": 1,
            "low_trust_threshold": 0.5,
            "recover_trust_threshold": 0.8,
            "high_risk_strategy": "eager",
        }

    normalized["strategies"].setdefault("eager", {})
    normalized["strategies"].setdefault("lazy", {})
    normalized["strategies"].setdefault("lease", {})
    normalized["strategies"].setdefault("exec_count", {})
    return _populate_runtime_aliases(normalized)


def load_scenario(scenario_path: str) -> Dict:
    """Load a YAML scenario file into a configuration dictionary.

    Parameters
    ----------
    scenario_path : str
        Path to the YAML scenario file.

    Returns
    -------
    dict
        Parsed scenario dictionary.
    """
    path = Path(scenario_path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data = validate_scenario(data, path)
    LOGGER.debug("event=scenario_loaded path=%s", path)
    return data
