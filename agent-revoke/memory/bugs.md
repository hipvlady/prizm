# Known Risks & Edge Cases

## RISK-001: Transient State Timeout Race

MESI transient states store `tick_entered`. Engine checks age each tick.
Transient states must resolve within 100 ticks (configurable).

## RISK-002: Exec-Count Off-By-One

`operations_used` increments AFTER checking `< max_operations` (strict less-than).
Exhausted state reached when `operations_used == max_operations`.

**The killer demo metric:** exec-count(N=50) -> exactly 50 unauthorized ops.

## RISK-003: Scope Attenuation Bypass

`delegate_capability` MUST raise `ScopeAttenuationError` if `child.scope` is not a subset of `parent.scope`.
Check happens before any state mutation.
