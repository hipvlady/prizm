# Project Execution Framework

## Execution Flow

Requirements → Task Breakdown → Dependency Analysis → Parallel Assignment → Execution → Verification

## Task Registry

| # | Task | Agent | Blocked By | Phase |
|---|------|-------|------------|-------|
| 1 | Core domain types (Capability, RevocationEvent, AgentState) | mesi-domain | — | A |
| 2 | MESI state machine + transition table | mesi-domain | #1 | B |
| 3 | Tick-based logical clock (ADR-002) | mesi-domain | #1 | B |
| 4 | AuthorityService (PDP) + cascade revocation | authority-runtime | #1, #3 | C |
| 5 | AgentRuntime (PEP) + local capability cache | authority-runtime | #1, #2 | C |
| 6 | TrustScorer + anomaly detection | authority-runtime | #1 | B |
| 7 | 4 revocation strategies (eager/lazy/lease/exec-count) | mesi-domain | #1, #2 | C |
| 8 | Simulation engine + message bus | simulation-scenario | #4, #5, #7 | D |
| 9 | 3 business scenario YAML configs | simulation-scenario | #8 | E |
| 10 | Terminal visualization (rich) | simulation-scenario | #8 | E |
| 11 | HTML comparison report (Jinja2 + Chart.js) | simulation-scenario | #8 | E |

## Execution Phases

Phase A:  #1
Phase B:  #2 ‖ #3 ‖ #6       (3 parallel)
Phase C:  #4 ‖ #5 ‖ #7       (3 parallel)
Phase D:  #8                   (integration)
Phase E:  #9 ‖ #10 ‖ #11     (3 parallel)

Critical path: #1 → #2 → #7 → #8 → #10

## Agent ↔ Phase Mapping

| Phase | mesi-domain-engineer | authority-runtime-engineer | simulation-scenario-engineer |
|-------|---------------------|---------------------------|------------------------------|
| A | #1 | — | — |
| B | #2, #3 | #6 | — |
| C | #7 | #4, #5 | — |
| D | — | — | #8 |
| E | — | — | #9, #10, #11 |

## Per-Task Verification

| Task | Verification |
|------|-------------|
| #1 | `python -c "from src.core.types import Capability, RevocationEvent, MESIState"` |
| #2 | `pytest tests/ -k mesi -v` |
| #3 | `pytest tests/ -k clock -v` |
| #4 | `pytest tests/ -k authority -v` — cascade BFS, scope attenuation |
| #5 | `pytest tests/ -k runtime -v` — action denied on Invalid, op limits |
| #6 | `pytest tests/ -k trust -v` — anomaly threshold at 0.3 |
| #7 | `pytest tests/ -k strategy -v` — all 4 strategies, staleness bounds |
| #8 | `pytest tests/ -k simulation -v` — grant→revoke→verify cycle |
| #9 | Scenario YAML loads without error, defines all required fields |
| #10 | Scenario runs with rich output matching expected log format |
| #11 | HTML report generates and contains Chart.js visualizations |

## Checkpoint Gates

After each phase completes, run before proceeding:
1. `python -m pytest tests/ -v` (full suite)
2. `python -m mypy src/ --strict`
3. `/enforce fix` — auto-fix formatting + lint (clears mechanical noise)
4. code-reviewer + security-correctness-reviewer (parallel):
   - code-reviewer: `/review --phase <current>` — quality, performance, maintainability
   - security-correctness-reviewer: invariant checks, coherence protocol correctness

## Rules

- Never skip a phase
- All tasks in a phase launch in a SINGLE message (parallel)
- Mark tasks in_progress before starting, completed when verified
- If a task fails verification, fix before unblocking dependents
- Update memory/decisions.md on architectural choices
- Update memory/bugs.md on discovered edge cases
