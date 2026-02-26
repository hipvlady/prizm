# Depth and Cascade Roadmap

This is the next implementation wave after the current demo baseline.

## Goal

Strengthen delegation-depth guarantees and formalise cascade properties with minimal TLA+ scope.

## Planned Additions

### 1. Minimal TLA+ Pack

Status: implemented.

Focus only on chain revocation invariants:

- Safety: revoked parent implies descendants are eventually invalid.
- Liveness: no capability remains in transient state beyond timeout.
- Bound: unauthorised actions per depth stay within strategy function.
- Files: `formal/tla/RevocationChain.tla`, `formal/tla/RevocationChain.cfg`.
- Runbook: `formal/tla/README.md`.

### 2. Cascade Correctness Guarantees for Pull Strategies

Status: next outstanding item.

- certificate semantics extended for consistency-directed modes (`lazy`, `lease`, `exec_count`),
- clearer eventual-completion interpretation in pull/check paths.

### 3. Report Template Split

Status: implemented.

- separate templates for single-strategy, comparison, and aggregated views.

## Why This Is Next

- Direct continuation of current metrics and scenario design.
- Strong judge narrative: root revoke with measurable cascade bounds.
- Feasible hackathon scope without full compositional interference proof.

## Out of Scope For This Wave

- Full compositional proof across arbitrary N-agent interference.
- Full OIDC/SCIM integration.
- Byzantine partition modelling.
