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
- .claude/agents/security-correctness-reviewer.md -> pre-checkpoint gate

## Demo Checkpoint Order

Step1 -> Step2 -> Step3 -> Step4 -> Step5 -> Step6

Never skip. Each checkpoint is independently demonstrable.

## Execution Phases (Parallel Opportunities)

Build order allows parallelism; checkpoint order stays sequential.

```
Phase A: Step 1 (foundation)          — mesi-domain-engineer
Phase B: Step 2 ‖ Step 3              — authority-runtime-engineer ‖ mesi-domain-engineer
Phase C: Step 4 (wires strategies+runtime) — simulation-scenario-engineer
Phase D: Step 5 ‖ Step 6              — simulation-scenario-engineer (split)
```

| Phase | Parallel? | Why |
|-------|-----------|-----|
| A→B | Step 2 ‖ Step 3 | Both depend only on Step 1 types. Different files, no shared state. |
| C | Sequential | Needs both strategies (Step 3) and runtime (Step 2). |
| C→D | Step 5 ‖ Step 6 | Both consume simulation output. Independent renderers (`terminal.py` vs `report.py`). |

Launch parallel steps in a **single message** with multiple Task tool calls.


<claude-mem-context>

</claude-mem-context>