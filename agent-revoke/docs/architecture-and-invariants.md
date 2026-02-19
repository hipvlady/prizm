# Architecture and Invariants

## System Components

- `AuthorityService` (`src/authority/service.py`): canonical capability lifecycle (grant/delegate/revoke).
- `CapabilityRegistry` (`src/authority/registry.py`): authority-side source of truth.
- `RevocationBroadcaster` (`src/authority/broadcaster.py`): revocation message fanout with configurable latency/loss.
- `AgentRuntime` (`src/agent/runtime.py`): local cache and action validation path.
- Strategies (`src/strategies/*.py`): coherence policy implementations.
- `SimulationEngine` (`src/simulation/engine.py`): tick loop, scenario execution, and instrumentation.
- `ConsistencyMonitor` (`src/simulation/consistency.py`): convergence and staleness tracking.
- `MetricsCollector` (`src/simulation/metrics.py`): aggregated run metrics.

## Data and Message Flow

1. Authority grants root capability.
2. Delegation creates a chain (`parent_cap_id`, `delegation_depth`).
3. Revocation event is issued.
4. Broadcaster delivers messages with simulated latency.
5. Agents validate actions via chosen strategy.
6. Metrics record authorised/unauthorised outcomes and latency indicators.

## Delegation Policy Gate

Policy is modelled by `DelegationPolicy` and enforced in `AuthorityService.delegate_capability`.

Enforced constraints:

- `child_depth <= max_depth`
- `child_scope subset_of parent_scope` (when enabled)
- `child.max_operations <= parent.remaining_operations` (when enabled)

Domain-specific failures:

- `DelegationDepthExceededError`
- `RemainingOpsPropagationError`
- `ScopeAttenuationError`

## Implemented Invariants

### Depth Policy

- Child depth is parent depth + 1.
- Delegation above configured depth is rejected.

### Scope Attenuation

- Child scope cannot exceed parent scope when subset requirement is enabled.

### Remaining Operations Propagation

- Delegation from exhausted parent operation budget is rejected.
- Operation counters are monotonic in cache mutation path.

### Cascade Certificate Fields

`RevocationEvent` tracks:

- `expected_capabilities`
- `invalidated_capabilities`
- `cascade_completion_tick`

This gives machine-readable evidence for cascade progress in push paths.

## Strategy Semantics (Current)

- `eager`: push invalidation accepted immediately at agent runtime (`accepts_push_revocation=True`).
- `lazy`, `lease`, `exec_count`: consistency-directed and action-time checked.

Important: cascade completeness ratio is currently strongest for push path (`eager`). For pull/check paths it does not yet represent full eventual convergence semantics.

## Transient-State Liveness Guard

ADR-005 is implemented in cache timeout checks:

- if transient state age exceeds configured timeout,
- force transition to `Invalid`.

This prevents indefinite transient lock-in under message-loss or delayed completion.
