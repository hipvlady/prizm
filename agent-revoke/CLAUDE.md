# agent-revoke

MESI cache coherence adapted for multi-agent authorization. Python 3.11+, ~10h budget.

## Read First

- `memory/decisions.md` — ADRs
- `memory/bugs.md` — known risks
- `memory/key_facts.md` — stack, invariants, time budget

## Invariants

1. `child.scope ⊆ parent.scope` — raise `ScopeAttenuationError` on violation
2. `child.max_operations ≤ parent.remaining_operations`
3. `operations_used` monotonic — never decrement
4. Cascade: BFS only, no recursive DFS
5. Eager: block until ALL agents ACK
6. `max_operations=None` = unbounded, not zero

## Agents → Ownership

| Agent | Scope |
|-------|-------|
| `mesi-domain-engineer` | `src/core/*`, `src/strategies/*` |
| `authority-runtime-engineer` | `src/authority/*`, `src/agent/*` |
| `simulation-scenario-engineer` | `src/simulation/*`, `src/output/*`, `scenarios/` |
| `security-correctness-reviewer` | pre-checkpoint gate |

## Checkpoints

Step1 → Step2 → Step3 → Step4 → Step5 → Step6. Sequential, never skip.

## Parallelism

```
A: Step 1                    — foundation
B: Step 2 ‖ Step 3           — different files, no shared state
C: Step 4                    — wires strategies + runtime
D: Step 5 ‖ Step 6           — independent renderers
```

Launch parallel steps in a single message with multiple Task calls.

## Workflow

- Complex tasks: plan mode first, get approval, then implement
- Break large changes into reviewable chunks
- Run `security-correctness-reviewer` before every checkpoint

## Verify Before Done

- `python3.11 -m pytest tests/ -v` after code changes
- `python3.11 -m mypy src/ --strict` before marking complete
- Scenario changes: run `simulate --scenario=<name>`, confirm expected metrics
- Strategy changes: verify MESI transitions in test output match transition table

## Learnings

PR review findings and session discoveries. Update via `@.claude` on PRs or `#` shortcut.

<!-- Add entries as: - YYYY-MM-DD: learning -->