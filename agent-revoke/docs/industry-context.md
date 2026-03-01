# Industry Context

## Why This Problem Is Practical

Agentic IAM systems increasingly use delegated credentials and cached decisions for performance. Revocation lag creates a measurable attack window. At human velocity this window is operationally negligible; at agent velocity (100-10,000 ops/s) it becomes a first-order security concern.

CCS (Capability Coherence System) provides a formal framework for reasoning about this window. This document maps CCS contributions to existing industry standards and frameworks.

---

## Cloud Security Alliance -- Agentic IAM Framework

The CSA Agentic IAM framework defines five pillars for securing agent-to-agent authorization. CCS operationalizes each pillar through measurable protocol guarantees.

| CSA Pillar | CCS Implementation | Measured Outcome |
|---|---|---|
| **Continuous Verification** | Consistency-directed strategies (`lazy`, `lease`, `exec_count`) enforce periodic re-validation against the authority | Staleness window bounded per strategy; exact bounds in CRM scenario (sigma=0) |
| **Least Privilege** | Delegation policy gate enforces scope attenuation (`child.scope subset parent.scope`), depth limits, and operation budget propagation | `ScopeAttenuationError`, `DelegationDepthExceededError`, `RemainingOpsPropagationError` on violation |
| **Behavior-based Authorization** | Trust scorer evaluates action history; anomaly detection triggers automatic revocation | Anomaly scenario demonstrates trust-driven revocation path with measurable impact comparison |
| **Trust Scoring** | Dynamic per-agent trust score with configurable decay on anomaly and recovery thresholds | Adaptive strategy mode switches agents to stricter strategy when trust drops below threshold |
| **JIT Access** | Ephemeral credential lifetimes by time (`lease.ttl`) or operation count (`exec_count.max_operations`) | RCC credentials self-invalidate at operation boundary, forcing re-acquisition from authority |

### What CCS adds to CSA

CSA prescribes *what* to do (continuous verification, least privilege, trust scoring). CCS provides *how to measure whether you are doing it* -- concrete metrics (unauthorized actions, staleness windows, cascade completion ratios) that quantify compliance with each pillar under specific strategy configurations.

---

## OpenID Foundation -- Agentic AI Whitepaper

The OpenID Foundation Agentic AI whitepaper identifies several challenges in delegated agent authorization. CCS addresses these directly.

### Execution-Count Bounds

The whitepaper motivates operation-bounded credentials as explicit impact control for delegated agents. CCS implements this as the RCC (Release-Consistent Credentials) strategy:

- The agent receives a capability with `max_operations = n`
- After *n* operations, the credential self-invalidates (transitions to Invalid)
- The agent must re-acquire from the authority to continue
- This is acquire/release semantics from release consistency theory, not rate limiting

**Key difference from rate limiting**: rate limiting rejects excess requests while the agent retains its stale credential. RCC invalidates the credential itself, forcing the agent to discover whether it has been revoked.

**Theorem 1 (per-capability safety bound)**: For RCC with budget *n*, unauthorized operations *D <= n*, independent of agent velocity. This is confirmed with sigma=0 in the deterministic CRM scenario and zero bound violations across 120 experimental runs.

### Revocation Propagation in Delegation Chains

The whitepaper identifies revocation propagation across delegated/offline chains as an unresolved challenge. CCS addresses this with:

- **BFS cascade traversal** (ADR-004): when a root capability is revoked, the authority computes all descendants via BFS and issues targeted revocation events
- **Two-phase cascade certificate**: tracks delivery completion (all agents notified) separately from local completion (all capabilities transitioned to stable Invalid)
- **Per-depth unauthorized bound**: `f(strategy, d)` provides strategy-specific damage bounds at each delegation depth

### On-Behalf-Of (OBO) Delegation

CCS models OBO delegation through capability chains:
- `Capability.delegator_id` tracks who delegated
- `Capability.parent_cap_id` links to the parent capability
- Scope attenuation ensures child capabilities cannot exceed parent permissions
- `CapabilityRegistry.get_delegation_chain()` provides BFS traversal of the delegation DAG

### Shared Signals Framework

The `RevocationBroadcaster` propagation model is conceptually aligned with the Shared Signals Framework (SSF). Both define an event-driven propagation mechanism for security state changes across trust domains. CCS uses a simulated network with configurable latency and loss; a production mapping to SSF/SET (Security Event Tokens) is a planned integration point.

---

## OpenFGA / Oso -- Delegated Access Patterns

OpenFGA and Oso document the latency-vs-freshness trade-off that arises in production authorization systems. CCS validates this trade-off formally and quantifies its security implications at agent velocity.

### Latency vs Freshness Spectrum

Production authorization systems navigate a spectrum between:
- **Strict consistency** (every action checked against the authority): lowest latency window, highest coordination cost
- **Eventual consistency** (cached decisions with periodic refresh): highest throughput, widest staleness window

CCS formalizes this spectrum through four strategies:

| Strategy | Consistency Model | Trade-off |
|---|---|---|
| `eager` | Strict (push invalidation) | Lowest staleness, highest message overhead |
| `lazy` | Periodic pull | Bounded by check interval + propagation delay |
| `lease` | Time-bounded cache | Bounded by TTL window -- velocity-dependent damage |
| `exec_count` | Operation-bounded cache | Bounded by operation budget -- velocity-independent damage |

### Policy Choice by Risk Profile

Oso emphasizes selecting authorization policy based on workload risk profile (e.g., payments vs CRM sync). CCS supports this through:

- **Heterogeneous strategy mode**: different agents receive different strategies based on their role (e.g., `banking: eager`, `crm: lease`, `analytics: lazy`, `api: exec_count`)
- **Adaptive strategy mode**: agents automatically switch to a stricter strategy when their trust score drops below a configurable threshold

This aligns with the principle that authorization consistency requirements should match the risk profile of the operation being authorized.

### Quantified Evidence

CCS provides the quantitative evidence that production systems lack:

| Scenario | Lease (TTL) | RCC (exec_count) | Reduction |
|---|---:|---:|---|
| CRM high-velocity (100 ops/tick) | 6,000 unauthorized | 50 unauthorized | **120x** |
| Anomaly auto-revocation | 2,951 unauthorized | 16 unauthorized | **184x** |

These numbers demonstrate that the latency-vs-freshness trade-off has concrete, measurable security implications at agent velocity -- it is not merely a performance concern.

---

## Ping Identity -- Agent Delegation Guidance

Ping Identity guidance on agent delegation emphasizes two principles:

1. **Delegation must remain auditable and distinct from impersonation.** CCS enforces this through the delegation chain model: every capability tracks its `delegator_id`, `parent_cap_id`, and `delegation_depth`. Delegation is a first-class relationship, not a proxy.

2. **Behavior monitoring plus automatic controls are practical defaults.** CCS implements this through the trust scorer and anomaly detection pipeline: `TrustScorer.check_anomaly()` evaluates agent behavior, and anomaly detection in the simulation engine triggers automatic revocation when trust scores cross configurable thresholds.

---

## Summary: CCS Position in the Landscape

| Framework/Standard | What They Define | What CCS Adds |
|---|---|---|
| **CSA Agentic IAM** | Pillars: continuous verification, least privilege, trust scoring | Measurable metrics per pillar; strategy comparison shows which approaches satisfy each pillar and at what cost |
| **OpenID Agentic AI** | Challenges: execution bounds, revocation propagation, OBO delegation | Formal RCC strategy with Theorem 1 safety bound; BFS cascade with per-depth metrics; delegation DAG model |
| **OpenFGA / Oso** | Trade-off: latency vs freshness in authorization | Quantified security impact at agent velocity; heterogeneous/adaptive strategy selection by risk profile |
| **Ping Identity** | Principles: auditability, behavior monitoring | Delegation chain model with full provenance; trust scorer with automatic revocation |

CCS does not replace any of these frameworks. It provides a **simulation and measurement layer** that quantifies the security implications of authorization design choices under agent velocity conditions -- enabling evidence-based strategy selection rather than heuristic configuration.
