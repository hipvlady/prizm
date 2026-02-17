# agent-revoke — CLAUDE.md

## Project

Temporal consistency in multi-agent authorization via MESI cache coherence adaptation.
Python 3.11+. Solo hackathon, ~10h budget.

## Memory — Read Before Every Task

- memory/decisions.md (ADRs)
- memory/bugs.md (known risks)
- memory/key_facts.md (stack + invariants + time budget)

## Critical Invariants — Never Violate

1. child.scope ⊆ parent.scope (scope attenuation, raise ScopeAttenuationError if violated)
2. child.max_operations ≤ parent.remaining_operations
3. operations_used is monotonic — never decremented
4. Cascade revocation uses BFS, not recursive DFS
5. Eager strategy blocks until ALL agents ACK (consistency-agnostic)
6. max_operations=None means unbounded, not zero

## Subagents

- .claude/agents/mesi-domain-engineer.md -> src/core/*, src/strategies/*
- .claude/agents/authority-runtime-engineer.md -> src/authority/*, src/agent/*
- .claude/agents/simulation-scenario-engineer.md -> src/simulation/*, src/output/*, scenarios/
- .claude/agents/code-standards-enforcer.md -> tooling config, auto-fix, quality gates
- .claude/agents/code-reviewer.md -> all src/ (read-only), checkpoint gates + pre-PR
- .claude/agents/security-correctness-reviewer.md -> invariants, checkpoint gates

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

Critical path: #1 → #2 → #7 → #8 → #10. Launch parallel tasks in a single message.

See `.claude/rules/` for full execution framework, parallel checklist, and orchestration guide.
