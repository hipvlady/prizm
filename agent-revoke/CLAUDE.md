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

| `code-standards-enforcer` | tooling config, auto-fix, quality gates |
| `code-reviewer` | all `src/` (read-only), checkpoint gates + pre-PR |

## Task Breakdown

| # | Task | Agent | Blocked By | Phase |
|---|------|-------|------------|-------|
| 1 | Core domain types | mesi-domain | — | A |
| 2 | MESI state machine | mesi-domain | #1 | B |
| 3 | Logical clock | mesi-domain | #1 | B |
| 4 | AuthorityService (PDP) | authority-runtime | #1, #3 | C |
| 5 | AgentRuntime (PEP) + cache | authority-runtime | #1, #2 | C |
| 6 | TrustScorer | authority-runtime | #1 | B |
| 7 | 4 revocation strategies | mesi-domain | #1, #2 | C |
| 8 | Simulation engine + bus | simulation-scenario | #4, #5, #7 | D |
| 9 | 3 scenario configs | simulation-scenario | #8 | E |
| 10 | Terminal viz (rich) | simulation-scenario | #8 | E |
| 11 | HTML report (Jinja2) | simulation-scenario | #8 | E |

## Execution Phases

```
A: #1 → B: #2 ‖ #3 ‖ #6 → C: #4 ‖ #5 ‖ #7 → D: #8 → E: #9 ‖ #10 ‖ #11
```

Critical path: `#1 → #2 → #7 → #8 → #10`. Launch parallel tasks in a single message.

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
