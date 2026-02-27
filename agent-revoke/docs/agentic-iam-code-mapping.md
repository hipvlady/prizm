# Agentic IAM to Code Mapping

This file maps standards language to concrete implementation touchpoints.

## CSA Five Pillars

| CSA Pillar | Code path | Current implementation |
|---|---|---|
| Continuous Verification | `src/strategies/lazy.py::LazyInvalidationStrategy.validate_action` + `src/agent/runtime.py::AgentRuntime.attempt_action` | Pull-time re-check behavior on configured intervals. |
| Continuous Verification | `src/strategies/exec_count.py::ExecCountStrategy.record_action` + runtime revalidation path | Revalidation after operation budget exhaustion. |
| Least Privilege | `src/authority/service.py::AuthorityService.delegate_capability` | Enforces scope attenuation and depth guardrails. |
| Least Privilege | `src/core/types.py::DelegationPolicy` + `src/core/exceptions.py::BudgetExceededError` | Prevents delegating exhausted op budgets. |
| Behavior-based Auth | `src/authority/trust_scorer.py::TrustScorer.check_anomaly` + `src/simulation/engine.py::_run_anomaly_detection` | Anomalies trigger automatic revocation. |
| Trust Scoring | `src/authority/trust_scorer.py::TrustScorer.evaluate` + `src/core/types.py::AgentState.trust_score` | Dynamic score update from action history. |
| JIT Access | `src/authority/service.py::grant_capability(ttl=..., max_operations=...)` | Ephemeral credential lifetime by time or operation budget. |
| JIT Access | `src/strategies/exec_count.py` / `src/strategies/lease.py` revalidation behavior | Expiry or exhaustion forces fresh check. |

## OpenID Agentic Concepts

| OpenID concept | Code path |
|---|---|
| OBO / delegation chain | `Capability.delegator_id`, `Capability.parent_cap_id`, registry delegation traversal |
| Scope attenuation | `delegate_capability(... attenuated_scope=...)` subset check + `ScopeViolationError` |
| Execution-count bound | `ExecCountStrategy` + `Capability.max_operations` |
| Revocation propagation | `AuthorityService.revoke_capability(cascade=True)` + broadcaster fanout |
| Shared-signals-like propagation model | `RevocationBroadcaster` over simulated network queue |
| Offline token revocation | Not implemented in current scope (tracked stretch item) |
