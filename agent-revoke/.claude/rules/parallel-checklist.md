# Parallel Execution Checklist

## Pre-Task Checklist

Before starting any phase:
- [ ] All blocking tasks are completed and verified
- [ ] Memory files read (decisions.md, bugs.md, key_facts.md)
- [ ] Agent assignment matches task table
- [ ] Demo checkpoint for this phase is understood

## Dependency Quick-Check

Can these tasks run in parallel?

| Question | Yes → Parallel | No → Sequential |
|----------|---------------|-----------------|
| Different files/directories? | ✓ | Wait |
| No shared mutable state? | ✓ | Wait |
| Independent test suites? | ✓ | Wait |
| No output→input data flow? | ✓ | Wait |
| Different agent ownership? | ✓ (ideal) | Still OK if different files |

## Common Parallel Patterns in This Project

### Phase B — Foundation modules (after #1)
```
#2 (src/core/mesi.py) ‖ #3 (src/core/clock.py) ‖ #6 (src/authority/trust.py)
```
Why: Different files, all import only from src/core/types.py (read-only dependency).

### Phase C — Service layer (after Phase B)
```
#4 (src/authority/service.py) ‖ #5 (src/agent/runtime.py, cache.py) ‖ #7 (src/strategies/*.py)
```
Why: Different directories, no shared state. Authority uses clock, runtime uses MESI, strategies use MESI — all read-only imports.

### Phase E — Output layer (after #8)
```
#9 (scenarios/*.yaml) ‖ #10 (src/output/terminal.py) ‖ #11 (src/output/report.py)
```
Why: Different files, all consume simulation engine output (read-only).

### Sequential Chains — Never Parallel
```
#1 → #2 (MESI needs types)
#2 → #7 (strategies need MESI machine)
#4 + #5 + #7 → #8 (engine wires everything)
```

## Task Size Guide

| Size | Action | Example |
|------|--------|---------|
| < 10 lines, obvious | Do inline | Add missing import, fix typo |
| Clear scope, testable | Task unit ✓ | #2 MESI state machine, #6 TrustScorer |
| Multi-component, integration | Break down first | #8 = engine.py + bus.py |
| Entire layer | Already broken down | Phase C = 3 independent tasks |

## Red Flags — Stop and Reassess

- Task modifies files owned by a different agent → reassign or coordinate
- Two parallel tasks importing from each other → hidden dependency, sequence them
- Test failures in a dependency → don't start dependent tasks
- Invariant violation in checkpoint gate → fix before proceeding
- Task scope creeping beyond its phase → split into new task for later phase
- Agent needs types not yet defined in types.py → belongs in Phase A, not later
