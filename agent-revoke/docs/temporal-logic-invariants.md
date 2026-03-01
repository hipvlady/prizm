# Temporal Logic Invariants

This document captures the invariant formulas used to reason about the simulation and links them to implementation checks.

## Safety and Liveness Formulas

- SWMR authorization safety:
  - `AG(Revoked(c) -> AX !Authorized(c))`
- Bounded staleness safety:
  - `AG(Revoked(c) -> AF<=B !Authorized(c))`
- Transient-state liveness:
  - `AG(Transient(c) -> AF StableOrInvalid(c))`
- Cascade completeness:
  - `AG(Revoked(parent) -> AF (forall child in Desc(parent): Invalid(child)))`
- Scope attenuation:
  - `AG(Delegated(child,parent) -> Scope(child) subset Scope(parent))`
- Monotonic operation count:
  - `AG(OpsUsed(c,t+1) >= OpsUsed(c,t))`

## Mapping to Runtime Checks

- SWMR and stale-action accounting:
  - `SimulationEngine._run_agent_actions(...)`
  - `ConsistencyMonitor.record_unauthorized_action(...)`
- Bounded staleness depth checks:
  - `simulation/bounds.py` + `SimulationEngine._check_bound_violation(...)`
- Transient liveness fail-safe:
  - `AgentRuntime.check_transient_timeouts(...)`
- Cascade completeness certificate:
  - `RevocationEvent.expected_capabilities`
  - `RevocationEvent.invalidated_capabilities`
  - `ConsistencyMonitor` completion tick tracking
- Scope attenuation and budget propagation:
  - `AuthorityService.delegate_capability(...)`
  - `DepthExceededError`, `BudgetExceededError`, `ScopeViolationError`

## Formal Model Status

- Minimal model is implemented in:
  - `formal/tla/RevocationChain.tla`
  - `formal/tla/RevocationChain.cfg`
- Model checks include:
  - `CascadeSafety`
  - `TransientEventuallyInvalid`
  - `TransientAgeBound`
  - `UnauthorizedWithinBound`

Mechanized unbounded proof remains future research scope.
