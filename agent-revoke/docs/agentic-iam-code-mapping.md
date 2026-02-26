# Agentic IAM to Code Mapping

This file maps standards language to concrete implementation touchpoints.

## CSA Five Pillars

| CSA Pillar | Code path | Current implementation |
|---|---|---|
| Continuous Verification | `LazyInvalidationStrategy.validate_action()` + `AgentRuntime.attempt_action()` | Pull-time re-check behavior on configured intervals. |
| Continuous Verification | `ExecCountStrategy.record_action()` + runtime revalidation path | Revalidation after operation budget exhaustion. |
| Least Privilege | `AuthorityService.delegate_capability()` | Enforces scope attenuation and depth guardrails. |
| Least Privilege | `DelegationPolicy.propagate_remaining_ops` + `RemainingOpsPropagationError` | Prevents delegating exhausted op budgets. |
| Behavior-based Auth | `TrustScorer.check_anomaly()` + `SimulationEngine._run_anomaly_detection()` | Anomalies trigger automatic revocation. |
| Trust Scoring | `TrustScorer.evaluate()` + `AgentState.trust_score` | Dynamic score update from action history. |
| JIT Access | `AuthorityService.grant_capability(ttl=..., max_operations=...)` | Ephemeral credential lifetime by time or operation budget. |
| JIT Access | `ExecCountStrategy` / `LeaseBasedStrategy` revalidation behavior | Expiry or exhaustion forces fresh check. |

## OpenID Agentic Concepts

| OpenID concept | Code path |
|---|---|
| OBO / delegation chain | `Capability.delegator_id`, `Capability.parent_cap_id`, registry delegation traversal |
| Scope attenuation | `delegate_capability(... attenuated_scope=...)` subset check |
| Execution-count bound | `ExecCountStrategy` + `Capability.max_operations` |
| Revocation propagation | `AuthorityService.revoke_capability(cascade=True)` + broadcaster fanout |
| Shared-signals-like propagation model | `RevocationBroadcaster` over simulated network queue |
| Offline token revocation | Not implemented in current scope (tracked stretch item) |
