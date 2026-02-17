# Agent Orchestration

## Subagent Roster

| Agent | Scope | Phases |
|-------|-------|--------|
| mesi-domain-engineer | src/core/*, src/strategies/* | A, B, C |
| authority-runtime-engineer | src/authority/*, src/agent/* | B, C |
| simulation-scenario-engineer | src/simulation/*, src/output/*, scenarios/ | D, E |
| code-standards-enforcer | tooling config, auto-fix | checkpoint gates (before review) |
| code-reviewer | all src/ (read-only) | checkpoint gates, pre-PR |
| security-correctness-reviewer | invariant verification | checkpoint gates |

## Launch Protocol

### Parallel Phase Launch (MANDATORY)

All independent tasks in a phase MUST launch in a single message:

```
# Phase B — CORRECT: single message, 3 tool calls
Message 1: [Task: #2 mesi-domain] + [Task: #3 mesi-domain] + [Task: #6 authority-runtime]

# Phase B — WRONG: sequential messages (3x slower)
Message 1: [Task: #2]
Message 2: [Task: #3]  ← waits for #2 to finish
Message 3: [Task: #6]  ← waits for #3 to finish
```

### Sequential Phase Transitions

```
Phase A complete → verify → launch Phase B (all 3 parallel)
Phase B complete → verify → launch Phase C (all 3 parallel)
Phase C complete → verify → launch Phase D
Phase D complete → verify → launch Phase E (all 3 parallel)
```

### Checkpoint Gate Review Order

At each gate, run in sequence then parallel:
```
Step 1: /enforce fix              (auto-fix formatting + lint)
Step 2: [code-reviewer] ‖ [security-correctness-reviewer]    (parallel review)
```
Standards enforcer runs first to eliminate mechanical noise before human-style review.
Both reviewers must pass before advancing to the next phase.

## Subagent Instructions Template

Each subagent launch MUST include:
1. Task ID and description from the task registry
2. Files to create/modify (from agent scope)
3. Dependencies satisfied (list completed task IDs)
4. Invariants to enforce (from CLAUDE.md)
5. Verification command to run on completion

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Launch Phase C tasks in separate messages | Single message, 3 Task tool calls |
| Start #8 before #4, #5, #7 all pass tests | Wait for full Phase C verification |
| Let mesi-domain edit src/authority/ | Respect agent file ownership |
| Skip mypy after a phase | Run `mypy src/ --strict` at every gate |
| Retry same failing approach 3+ times | Escalate: read memory/bugs.md, consult ADRs |
| Create types outside src/core/types.py | All types exported from types.py (invariant) |
| Launch parallel tasks that share mutable state | Sequence them or refactor to read-only deps |
| Assume subagent remembers prior context | Include FULL context in every launch prompt |

## Task Granularity Sweet Spot

| Too Granular (just do it) | Just Right (task unit) | Too Broad (break down) |
|---------------------------|------------------------|------------------------|
| "Add MESIState.INVALID" | "#2 MESI state machine + transitions" | "Build entire core layer" |
| "Fix import in types.py" | "#6 TrustScorer + anomaly detection" | "Implement all strategies" |
| "Add test assertion" | "#10 Terminal visualization with rich" | "Build simulation + output" |
| "Rename variable" | "#4 AuthorityService + cascade BFS" | "Implement authority + runtime" |

Just right = atomic + testable + single-agent + 1-2h scope.

## Status Tracking

Use TaskUpdate to track execution:
- `pending` → task not started, dependencies may be unresolved
- `in_progress` → agent actively working, set BEFORE writing code
- `completed` → verified passing, set AFTER tests pass

Never mark completed if tests are failing or mypy has errors.
