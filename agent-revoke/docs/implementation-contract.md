# Implementation Contract

This document translates the consolidated specification into implementation-facing contracts for the current codebase.

## Scope

- Engine lifecycle and tick ordering
- Network transport behavior
- Metrics and aggregation payloads
- CLI entry points
- Error handling boundaries
- Test fixtures and matrix anchors

## Core Runtime Contracts

### `SimulationEngine`

Implementation: `src/simulation/engine.py`

- Constructor: `SimulationEngine(config, strategy_name, scenario_name)`
- Main lifecycle: `run() -> SimulationMetrics`
- Tick flow: message delivery, maintenance/timeouts, scheduled revoke, actions, adaptive strategy, anomaly detection, convergence recording.
- Scenario bootstrap: `_setup_scenario()` grants root capability and builds delegation chain.
- Bound accounting: `_check_bound_violation(depth)` uses `calculate_depth_bound(...)`.

### `Network`

Implementation: `src/simulation/network.py`

- Queue model: `deque[NetworkMessage]`
- `send(...)`: enqueues with `delivery_tick = current_tick + latency`; can drop messages using configured loss rate.
- `deliver_due(current_tick)`: emits all due messages and marks them delivered.
- Counters: `pending_count`, `message_overhead`, `latency_ticks`.

### `SimulationMetrics` and Collector

Implementation: `src/simulation/metrics.py` and `src/simulation/aggregation.py`

- End-of-run payload: `SimulationMetrics` includes unauthorized counts, per-depth breakdown, latency percentiles, transient metrics, convergence, message overhead, and bound-violation map.
- Multi-run aggregate payload: `AggregatedMetrics` in `simulation/aggregation.py` with `mean/std` fields used by comparison reporting.
- Collector APIs include `record_revocation_latency`, `record_transient_duration`, `record_convergence`, and `finalize(...)`.

## Scenario + Config Contract

- Canonical schema: `docs/scenario-schema.md`
- Validator/normalizer: `src/simulation/scenarios.py`
- Reference scenarios:
  - `scenarios/banking-cascade.yaml`
  - `scenarios/crm-bulk-ops.yaml`
  - `scenarios/anomaly-autorevoke.yaml`

## CLI Contract

### Single-run

Implementation: `python -m src.simulation.engine ...`

- Positional scenario path
- `--strategy` choices: `eager`, `lazy`, `lease`, `exec_count`
- `--log-level` choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Strategy comparison

Implementation: `scripts/run_strategy_comparison.py`

- `--scenario`, `--output`, `--strategies`, `--log-level`
- multi-run args: `--runs`, `--seed-start`
- optional dataset export: `--json-output` (dashboard payload)

## Error Handling Contract

Implementation: `src/core/exceptions.py`

- `RevocationError`
- `StaleCredentialError`
- `CacheMissError`
- `DelegationDepthExceededError`
- `RemainingOpsPropagationError`
- `ScenarioValidationError`

## Test Contract Anchors

- Shared fixtures: `tests/conftest.py`
- Strategy behavior: `tests/test_strategies.py`
- Scenario schema validation: `tests/test_scenarios.py`
- Pull/cascade completion: `tests/test_pull_cascade_completion.py`
- Multi-run aggregation/reporting: `tests/test_multi_run.py`

## Data Flow Reference

See `docs/architecture-and-invariants.md` for the inter-module flow and invariants table.
