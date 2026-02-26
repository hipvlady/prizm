# Scenario YAML Schema

`load_scenario()` now enforces schema validation before a simulation starts.

## Required Top-Level Blocks

- `simulation`
- `network`
- `scenario`
- `strategies`
- `trust`
- `delegation`
- `transient`

## Core Validation Rules

- `simulation.duration_ticks`: integer `>= 1`
- `simulation.num_agents`: integer `>= 1`
- `network.latency_ticks`: integer `>= 0`
- `network.message_loss_rate`: float in `[0.0, 1.0)`
- `transient.timeout_ticks`: integer `>= 1`
- One of:
  - `scenario.action_probability` in `[0.0, 1.0]`
  - `scenario.agent_velocity` integer `>= 1`
- `scenario.name`: non-empty string
- `scenario.delegation_depth`: integer `>= 0` and `< simulation.num_agents`
- `scenario.cascade_on_revoke`: boolean
- `scenario.revocation_tick`: integer `>= 0` or `null`
- `strategies.lazy.check_interval_ticks`: integer `>= 1` when set
- `strategies.lease.default_ttl_ticks`: integer `>= 1` when set
- `strategies.exec_count.max_operations`: integer `>= 1` when set
- `trust.*` scores: numeric values in `[0.0, 1.0]` when set
- `delegation.max_depth`: integer `>= 1` when set
- `delegation.require_scope_subset`: boolean when set
- `delegation.propagate_remaining_ops`: boolean when set

## Heterogeneous Block

Optional block:

```yaml
heterogeneous:
  enabled: true
  policy:
    banking: eager
    crm: lease
    analytics: lazy
    api: exec_count
  agent_roles: [banking, crm, analytics, api]
```

Validation:

- `heterogeneous.enabled`: boolean
- `heterogeneous.policy`: mapping of role -> strategy
- strategy values must be one of `eager`, `lazy`, `lease`, `exec_count`
- `heterogeneous.agent_roles`: list of strings

## Adaptive Strategy Block

Optional block:

```yaml
adaptive_strategy:
  enabled: true
  evaluate_interval_ticks: 1
  low_trust_threshold: 0.5
  recover_trust_threshold: 0.8
  high_risk_strategy: eager
```

Behavior:

- If trust score falls below `low_trust_threshold`, agent strategy switches to `high_risk_strategy`.
- If trust score rises above `recover_trust_threshold`, agent strategy returns to baseline assignment.

Validation:

- `adaptive_strategy.enabled`: boolean
- `adaptive_strategy.evaluate_interval_ticks`: integer `>= 1`
- `adaptive_strategy.low_trust_threshold`: float in `[0.0, 1.0]`
- `adaptive_strategy.recover_trust_threshold`: float in `[0.0, 1.0]` and `>= low_trust_threshold`
- `adaptive_strategy.high_risk_strategy`: one of `eager`, `lazy`, `lease`, `exec_count`

## Error Behavior

Invalid configs raise `ScenarioValidationError` and fail fast before any simulation tick runs.

## Legacy Compatibility

Loader still accepts legacy keys (`agents`, `latency_ticks`, `revocation_trigger_tick`, etc.) and normalizes them to canonical schema fields.
