# The Bureaucracy of Speed: Structural Equivalence Between Memory Consistency Models and Multi-Agent Authorization Revocation

[Official public paper link (arXiv)](https://arxiv.org/abs/2603.09875)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

---

## The Problem

IAM systems were designed for humans. Security protocols like OAuth 2.0 and OIDC assume that the damage a user can inflict during a 60-second revocation window is bounded by typing speed. Agentic AI breaks this assumption.

| Operator | Velocity | Damage in 60s TTL window |
|----------|----------|--------------------------|
| Human | ~1 req/s | ~60 unauthorized ops |
| AI agent | 100 ops/s | 6,000 unauthorized ops |
| Lambda-scale agent | 10K TPS | 600,000 unauthorized ops |

A revocation latency that is negligible for humans becomes catastrophic at machine speed. TTL-based credential systems treat both cases identically.

This gap is recognized across the identity and security community:
- The **Cloud Security Alliance** Agentic IAM framework calls for continuous verification and dynamic trust posture in agent-to-agent interactions
- The **OpenID Foundation** Agentic AI whitepaper highlights revocation propagation across delegated/offline chains as an unresolved challenge and motivates operation-bounded credentials
- **OpenFGA** and **Oso** illustrate latency-vs-freshness trade-offs in delegated authorization that become security-critical at agent velocity

## The Insight

Authorization revocation in multi-agent delegation chains is **operationally equivalent** to cache coherence in shared-memory multiprocessors under bounded-staleness semantics.

Every token and signed assertion is a **cached copy** of a permission that existed at some time *t_0*. When the authority revokes that permission, all cached copies become stale. This is a coherence problem -- the same class of problem that hardware engineers solved with MESI protocols.

**State mapping:**

| MESI (Hardware) | Authorization | Semantics |
|-----------------|---------------|-----------|
| Modified | Delegated Authority | Can sub-delegate capabilities |
| Exclusive | JIT Access | Sole credential holder |
| Shared | Role-Based Pooling | Multiple agents, read-only |
| Invalid | Revoked | No permitted operations |

## Key Contributions

1. **Formal equivalence.** A Capability Coherence System (CCS) with an explicit state-mapping function from MESI cache states to authorization states, proving operational equivalence under bounded-staleness semantics.

2. **Velocity Vulnerability metric.** Agent velocity as a first-class security parameter: *V_v = v . TTL*. Arithmetically simple, but it exposes a dimension absent from human-centric IAM literature.

3. **Operation-bounded credentials (RCC).** Grounded in release consistency theory, not rate limiting. RCC *invalidates the credential* at the synchronization boundary, forcing re-acquisition from the authority. The agent cannot resume without a fresh grant -- this is acquire semantics, not throttling. This directly addresses the execution-count bounds concept from the OpenID Foundation's Agentic AI whitepaper.

4. **Reproducible evaluation.** Four strategies across three scenarios, 10 runs per configuration (deterministic seeds 0-9), population standard deviation.

## Results at a Glance

### CRM High-Velocity (100 ops/tick, credential revoked at tick 0)

| Strategy | Unauthorized Ops | Velocity-Independent? |
|----------|------------------|-----------------------|
| Eager | 500.0 +/- 0 | No |
| Lazy | 2,400.0 +/- 0 | No |
| Lease (TTL) | **6,000.0 +/- 0** | No |
| RCC (n=50) | **50.0 +/- 0** | Yes |

**120x reduction** in unauthorized operations (Lease vs RCC).

### Anomaly Auto-Revocation (trust-score triggered)

| Strategy | Unauthorized Ops | Notes |
|----------|------------------|-------|
| Eager | 108.0 +/- 0 | Synchronous blocking hurts |
| Lazy | 10.8 +/- 3.6 | Outperforms eager (check < latency) |
| Lease | 2,950.8 +/- 3.6 | TTL never expires in window |
| RCC (n=100) | 16.0 +/- 3.7 | Bounded ceiling regardless of topology |

**184x reduction** (Lease vs RCC). Strategies do not form a simple linear ranking.

## Relation to Existing Work

### CSA Agentic IAM Framework

CCS operationalizes several CSA pillars through measurable protocol guarantees:
- **Continuous Verification** maps to consistency-directed strategies (lazy check intervals, lease TTL, RCC revalidation cycles)
- **Least Privilege** maps to scope attenuation and delegation depth enforcement
- **Behavior-based Authorization** maps to trust-score anomaly detection with automatic revocation
- **JIT Access** maps to ephemeral credential lifetimes by time or operation budget

### OpenFGA / Oso Delegated Authorization

CCS validates the latency-vs-freshness trade-off documented in production authorization systems, and quantifies its security implications at agent velocity. The four revocation strategies formalize the spectrum between strict consistency (eager) and eventual consistency (lease/TTL) that production systems navigate informally.

### OpenID Foundation Agentic AI

The RCC (execution-count) strategy directly implements the execution-count bounds concept from the OpenID Agentic AI whitepaper. CCS provides a formal framework for analyzing revocation propagation across delegation chains -- the challenge the whitepaper identifies as unresolved. The Shared Signals Framework maps conceptually to the `RevocationBroadcaster` propagation model.

## Scope and Honest Limitations

### Equivalence Scope

CCS establishes an **operational** equivalence, not a semantic isomorphism. Hardware MESI guarantees memory visibility through physical interconnect properties; CCS achieves analogous authorization visibility guarantees through protocol-level strategy constraints. The mapping preserves state transition structure and bounded-staleness invariants while introducing domain-specific extensions (trust scoring, delegation DAGs, scope attenuation) absent from the hardware domain. CCS is a *coherence-inspired authorization protocol*, not a full MESI instance.

### RCC vs Rate Limiting

The central distinction: rate limiting rejects excess requests while the agent **retains its stale credential**. RCC invalidates the credential itself at the operation boundary, forcing re-acquisition. Under rate limiting, a revoked agent is throttled but believes its credential is valid. Under RCC, the agent discovers revocation at the synchronization boundary and transitions to Invalid. The contribution is the **consistency model reinterpretation**, not the arithmetic.

### Theorem 1 Scope

The RCC safety bound *D <= n* applies **per capability**. In delegation chains where multiple agents hold distinct capabilities with independent budgets, total unauthorized operations across a cascade may vary with stochastic scheduling (banking scenario sigma=13.0), but each individual capability respects the deterministic bound. Zero bound violations across all 120 experimental runs confirm this.

### Authority Centralization

CCS assumes authority consistency strictly stronger than agent consistency, analogous to the reliable directory controller assumption in NUMA coherence protocols. Under network partition, agents operating on cached credentials continue within their strategy bounds. Authority recovery follows the same model as directory controller failover: pending revocations are replayed from a durable event log. Split-brain scenarios are deferred to future work on replicated authority services.

### Adversarial Model

RCC bounds the *quantity* of unauthorized operations, not their *semantic impact*. A strategic adversary could select which *n* operations to execute for maximum damage. Adversarial operation scheduling within the execution budget -- analogous to cache-timing side channels in hardware coherence -- is an open problem.

### Evaluation Realism

Deterministic seeds isolate strategy-level effects from scheduling artifacts. Adversarial scheduling (worst-case operation timing within strategy bounds) is future work. The CRM scenario exhibits sigma=0 across ALL strategies because action scheduling is deterministic, confirming that the damage bounds are exact, not stochastic approximations. Banking and anomaly scenarios provide genuine cross-seed variance.

## Project Structure

```
agent-revoke/           Core simulator
  src/
    core/               Types, MESI states, clock, exceptions
    agent/              AgentRuntime (PEP), credential cache
    authority/          AuthorityService (PDP), trust scorer, broadcaster
    strategies/         eager, lazy, lease, exec_count
    simulation/         Engine, scenarios, metrics, consistency checks
    output/             Terminal display, HTML reports
  scenarios/            YAML scenario configs
  tests/                pytest suite (88% coverage)
  scripts/              Strategy comparison runner
  docs/                 Architecture, threat model, MESI mapping
  formal/tla/           TLA+ model with TLC configuration
  web/dashboard/        React dashboard for interactive analysis
```

## Quick Start

```bash
# Install
cd agent-revoke && pip install -r requirements.txt

# Run tests
pytest -q

# Run a single simulation
python -m src.simulation.engine scenarios/banking-cascade.yaml --strategy eager

# Generate comparison report
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output crm-comparison.html \
  --runs 10 --seed-start 0

# Export dashboard dataset
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --json-output /tmp/crm-dashboard.json \
  --runs 10 --seed-start 0
```

## Roadmap

- Broader TLA+ model beyond minimal chain (multi-agent interference)
- Shared Signals Framework / OIDC-A protocol mapping
- Scale evaluation to 50-100 agents
- Byzantine fault injection and adversarial scheduling
- Replicated authority service (split-brain resilience)

## Paper

The accompanying paper is available as:
- [**"The Bureaucracy of Speed: Structural Equivalence Between Memory Consistency Models and Multi-Agent Authorization Revocation"**](https://arxiv.org/abs/2603.09875)
- Subjects: cs.MA, cs.CR, cs.DC

## License

Apache-2.0. See [LICENSE](LICENSE).
