# Depth and Cascade Roadmap

## Goal

Strengthen delegation-depth guarantees and formalize cascade properties.

## Completed

### 1. Minimal TLA+ Pack

Status: **implemented**.

Focus on chain revocation invariants:

- Safety: revoked parent implies descendants are eventually invalid.
- Liveness: no capability remains in transient state beyond timeout.
- Bound: unauthorized actions per depth stay within strategy function.
- Files: `formal/tla/RevocationChain.tla`, `formal/tla/RevocationChain.cfg`.
- Runbook: `formal/tla/README.md`.

### 2. Cascade Correctness Guarantees for Pull Strategies

Status: **implemented**.

- Certificate semantics extended for consistency-directed modes (`lazy`, `lease`, `exec_count`).
- Clearer eventual-completion interpretation in pull/check paths.

### 3. Report Template Split

Status: **implemented**.

- Separate templates for single-strategy, comparison, and aggregated views.

## Planned

### 4. Broader TLA+ Model

Extend beyond minimal chain to cover multi-agent interference and wider topologies.

### 5. Shared Signals / OIDC-A Mapping

Explicit protocol mapping from CCS `RevocationBroadcaster` to SSF/SET event format.

### 6. Scale Evaluation

Evaluate system behavior at 50-100 agents to identify coordination overhead breakpoints.

## Out of Scope (Current Phase)

- Full compositional proof across arbitrary N-agent interference.
- Full OIDC/SCIM integration.
- Byzantine partition modeling.
