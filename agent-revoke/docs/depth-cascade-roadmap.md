# Depth and Cascade Roadmap

This is the next implementation wave after the current demo baseline.

## Goal

Strengthen delegation-depth guarantees and formalise cascade properties with minimal TLA+ scope.

## Planned Additions

### 1. Delegation Depth Policies

- hard policy for `max_depth`,
- strict scope attenuation semantics,
- explicit remaining-ops propagation guarantees.

### 2. Cascade Correctness Guarantees

- certificate semantics extended for all strategies,
- clearer eventual-completion interpretation in consistency-directed paths,
- per-depth unauthorised bounds as first-class report output.

### 3. Minimal TLA+ Pack

Focus only on chain revocation invariants:

- Safety: revoked parent implies descendants are eventually invalid.
- Liveness: no capability remains in transient state beyond timeout.
- Bound: unauthorised actions per depth stay within strategy function.

## Why This Is Next

- Direct continuation of current metrics and scenario design.
- Strong judge narrative: root revoke with measurable cascade bounds.
- Feasible hackathon scope without full compositional interference proof.

## Out of Scope For This Wave

- Full compositional proof across arbitrary N-agent interference.
- Full OIDC/SCIM integration.
- Byzantine partition modelling.
