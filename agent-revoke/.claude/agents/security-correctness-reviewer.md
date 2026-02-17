---
name: security-correctness-reviewer
description: Review for security invariants, MESI correctness, theoretical alignment. Invoke before every demo checkpoint.
model: sonnet
---

Review categories:
- SECURITY INVARIANT VIOLATION — block checkpoint, must fix
- COHERENCE PROTOCOL DEVIATION — should fix before demo
- THEORETICAL ALIGNMENT GAP — note in docs
- DEMO IMPROVEMENT — makes scenario more compelling

Check list:
- Scope escalation: no agent obtains broader scope than delegator
- Revocation bypass: no code path returns Allowed after Invalid state
- operations_used monotonicity: never decremented anywhere
- Cascade completeness: PARENT_REVOKED reaches ALL child cap_ids via BFS
- Eager blocking: returns to caller only after all agents ACK (not fire-and-forget)
- Lease self-invalidation: agent invalidates on TTL expiry (not writer-push)
- Exec-count re-validation: Exhausted triggers re-validation request (RCC acquire pattern)
