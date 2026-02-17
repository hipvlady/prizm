Run security-correctness-reviewer on $ARGUMENTS before checkpoint.

Spawn security-correctness-reviewer to check:
1. Scope attenuation: grep for delegate_capability, verify ScopeAttenuationError raised on violation
2. Revocation bypass: trace attempt_action -> MESI state check, confirm no Allowed after Invalid
3. operations_used monotonicity: grep for operations_used, verify no decrement
4. Cascade BFS: verify broadcaster.py uses queue/deque, not recursion

Output: pass/fail per invariant with file:line references.
Block checkpoint if any SECURITY INVARIANT VIOLATION finding exists.
