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
