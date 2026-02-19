# Industry Context

## Why This Problem Is Practical

Agentic IAM systems increasingly use delegated credentials and cached decisions for performance. Revocation lag creates a measurable attack window.

## Framing Sources

### OpenID Agentic AI

- Highlights revocation propagation across delegated/offline chains as unresolved.
- Motivates operation-bounded credentials as explicit impact control.

### CSA Agentic IAM

- Emphasises continuous verification and dynamic trust posture.
- Supports anomaly-triggered revocation as standard control.

### Oso and Production Authorisation

- Illustrates latency-vs-freshness trade-offs by workload.
- Reinforces policy choice by risk profile (for example payments vs CRM sync).

### Ping Identity Guidance

- Delegation must remain auditable and distinct from impersonation.
- Behaviour monitoring plus automatic controls are practical defaults.

## How `agent-revoke` Uses This Context

- Compares strict vs relaxed revocation consistency models.
- Quantifies post-revoke impact with deterministic and stochastic scenarios.
- Adds delegation-depth analysis so chain effects are explicit.
