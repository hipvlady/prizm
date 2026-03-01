# Threat Model

## Threat 1: Banking Cascade Delay

- **Trigger**: Root capability in a delegation chain is revoked.
- **Risk**: Downstream delegees keep acting before local cache invalidation.
- **Controls implemented**:
  - BFS cascade traversal (ADR-004)
  - Strategy comparison under controlled latency
  - Per-depth unauthorized action tracking
  - Two-phase cascade certificate (delivery completion vs local completion)
- **Residual risk**:
  - Consistency-directed strategies depend on check cadence / TTL / ops budget
  - Cascade completion time grows with delegation depth and network latency

## Threat 2: High-Velocity Credential Compromise

- **Trigger**: Compromised agent continues high-rate actions after credential revocation.
- **Risk**: Very large post-revoke volume in short time (Velocity Vulnerability: V_v = v . TTL).
- **Controls implemented**:
  - Deterministic high-velocity scenario (CRM: 100 ops/tick)
  - Operation-count strategy (`exec_count`) with strict cap
  - Bound checker with per-depth support
  - Zero bound violations confirmed across 120 experimental runs
- **Quantified impact**:
  - Lease (TTL): 6,000 unauthorized ops
  - RCC (n=50): 50 unauthorized ops (120x reduction)

## Threat 3: Behavioral Anomaly Window

- **Trigger**: Agent behavior deviates (timing/volume patterns).
- **Risk**: Delayed detection and response.
- **Controls implemented**:
  - Trust scorer with configurable anomaly checks
  - Automatic revocation trigger path
  - Adaptive strategy switching (trust-driven)
- **Residual risk**:
  - Anomaly detection accuracy depends on scorer configuration
  - Current implementation uses simulation approximation

## Threat 4: Delegation Chain Abuse

- **Trigger**: Agent creates deeply nested or overly permissioned delegation chains.
- **Risk**: Blast radius expansion through uncontrolled sub-delegation.
- **Controls implemented**:
  - `DelegationPolicy.max_depth` enforcement
  - Scope attenuation (child scope must be subset of parent)
  - Remaining operations propagation (child budget capped by parent residual)
  - Domain-specific errors: `DelegationDepthExceededError`, `ScopeAttenuationError`, `RemainingOpsPropagationError`

## Threat 5: Network Partition / Message Loss

- **Trigger**: Revocation messages lost or delayed.
- **Risk**: Agents operate on stale credentials indefinitely.
- **Controls implemented**:
  - Transient-state timeout fail-safe (ADR-005): forces transition to Invalid after configurable timeout
  - Message loss simulation (`network.message_loss_rate`) in all scenarios
  - Strategy-specific transient action policy (deny vs strategy-dependent)
- **Residual risk**:
  - Authority partition recovery (durable event log replay) is modeled but not fully implemented
  - Split-brain scenarios deferred to future work

## Threat 6: Adversarial Operation Scheduling

- **Trigger**: Strategic adversary selects which *n* operations to execute for maximum damage.
- **Risk**: RCC bounds the *quantity* of unauthorized operations but not their *semantic impact*.
- **Controls**: None currently -- analogous to cache-timing side channels in hardware coherence.
- **Status**: Open problem, acknowledged in paper limitations.

## Security Posture Summary

CCS quantifies the security implications of authorization design choices under agent velocity conditions. It is a simulation and measurement framework providing evidence-based strategy selection, not a production IAM system.
