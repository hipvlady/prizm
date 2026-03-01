# Agentic IAM to Code Mapping

This file maps standards language to concrete implementation touchpoints. For the full analysis of how CCS relates to each framework, see [`industry-context.md`](industry-context.md).

## CSA Agentic IAM -- Five Pillars

| CSA Pillar | Code path | Implementation |
|---|---|---|
| Continuous Verification | `LazyInvalidationStrategy.validate_action()` + `AgentRuntime.attempt_action()` | Pull-time re-check behavior on configured intervals |
| Continuous Verification | `ExecCountStrategy.record_action()` + runtime revalidation path | Revalidation after operation budget exhaustion |
| Least Privilege | `AuthorityService.delegate_capability()` | Enforces scope attenuation and depth guardrails |
| Least Privilege | `DelegationPolicy.propagate_remaining_ops` + `RemainingOpsPropagationError` | Prevents delegating exhausted op budgets |
| Behavior-based Auth | `TrustScorer.check_anomaly()` + `SimulationEngine._run_anomaly_detection()` | Anomalies trigger automatic revocation |
| Trust Scoring | `TrustScorer.evaluate()` + `AgentState.trust_score` | Dynamic score update from action history |
| JIT Access | `AuthorityService.grant_capability(ttl=..., max_operations=...)` | Ephemeral credential lifetime by time or operation budget |
| JIT Access | `ExecCountStrategy` / `LeaseBasedStrategy` revalidation behavior | Expiry or exhaustion forces fresh check |

## OpenID Foundation Agentic AI -- Concepts

| OpenID Concept | Code Path | Notes |
|---|---|---|
| OBO / delegation chain | `Capability.delegator_id`, `Capability.parent_cap_id`, `CapabilityRegistry.get_delegation_chain()` | Full provenance via BFS traversal of delegation DAG |
| Scope attenuation | `delegate_capability(... attenuated_scope=...)` subset check | Enforced at delegation time with `ScopeAttenuationError` |
| Execution-count bound | `ExecCountStrategy` + `Capability.max_operations` | RCC semantics -- credential self-invalidation, not rate limiting |
| Revocation propagation | `AuthorityService.revoke_capability(cascade=True)` + broadcaster fanout | BFS cascade with two-phase completion certificate |
| Shared Signals alignment | `RevocationBroadcaster` over simulated network queue | Conceptual SSF/SET mapping -- production integration planned |
| Offline token revocation | -- | Not implemented (planned roadmap item) |

## OpenFGA / Oso -- Delegated Access Patterns

| Concept | Code Path | Notes |
|---|---|---|
| Latency vs freshness trade-off | 4 strategies with different consistency models | Quantified in CRM scenario: 120x reduction (lease vs RCC) |
| Policy by risk profile | `StrategySelector` + heterogeneous mode config | Per-role strategy assignment in scenario YAML |
| Adaptive consistency | `adaptive_strategy` config block + engine integration | Trust-driven strategy switching at runtime |
| Cached authorization decisions | `AgentCache` with MESI state tracking | Local cache with strategy-specific invalidation semantics |
