# agent-revoke

Temporal consistency simulator for multi-agent authorisation revocation, inspired by MESI coherence and consistency-directed protocols.

## For Judges

This project demonstrates one core security question in Agentic IAM:

- A capability is revoked at the authority.
- Agents may still act on stale local cache state.
- We need bounded staleness and measurable impact.

`agent-revoke` compares four revocation strategies (`eager`, `lazy`, `lease`, `exec_count`) under repeatable scenarios and reports:

- unauthorised actions,
- staleness window,
- revocation latency,
- cascade behaviour by delegation depth,
- clock-dependence profile.

## What Is Implemented

- Python 3.11+ simulator with typed domain model (`dataclasses` + `Enum`).
- PDP/PEP split:
  - `AuthorityService` (policy decision point)
  - `AgentRuntime` (policy enforcement point)
- Four pluggable strategies:
  - `eager` (consistency-agnostic)
  - `lazy` (consistency-directed)
  - `lease` (time-bound, clock-dependent)
  - `exec_count` (operation-bound, clock-independent)
- Delegation policy controls:
  - `max_depth`
  - scope attenuation enforcement
  - remaining operation propagation
- BFS cascade traversal and cascade certificate fields:
  - `expected_capabilities`
  - `invalidated_capabilities`
  - `cascade_completion_tick`
- Per-depth bound checker:
  - `unauthorised_actions(depth=d) <= f(strategy, d)`
- HTML comparison report (Pico.css + Chart.js).
- Automated tests and coverage.

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run tests

```bash
pytest -q
```

### 3. Run one simulation

```bash
python -m src.simulation.engine scenarios/banking-cascade.yaml --strategy eager --log-level INFO
```

### 4. Generate strategy comparison report

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output crm-comparison.html \
  --log-level ERROR
```

## Judge Demo Flow (5 minutes)

### 1. CRM high-velocity scenario (main evidence)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --log-level ERROR
```

Open `/tmp/crm-comparison.html`.

Deterministic sample output captured on **19 February 2026**:

- `eager`: unauthorised `500`
- `lazy`: unauthorised `2400`
- `lease`: unauthorised `6000`
- `exec_count`: unauthorised `50`

### 2. Banking cascade scenario (depth propagation)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/banking-cascade.yaml \
  --output /tmp/banking-comparison.html \
  --log-level ERROR
```

Open `/tmp/banking-comparison.html` and inspect depth table.

### 3. Anomaly auto-revocation scenario

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/anomaly-autorevoke.yaml \
  --output /tmp/anomaly-comparison.html \
  --log-level ERROR
```

## Quality Signals

- Tests: `72 passed` (latest local run).
- Coverage: `88%` total (`coverage run -m pytest && coverage report -m`).
- Exceptions are domain-specific (`RevocationError`, `StaleCredentialError`, `CacheMissError`, etc.).
- Structured logging with severity levels (`DEBUG`/`INFO`/`WARNING`/`ERROR`).
- Latency instrumentation uses `time.perf_counter()`.

## Documentation Pack

Start here:

- `docs/README.md`
- `docs/judges-guide.md`
- `docs/architecture-and-invariants.md`
- `docs/metrics-and-evidence.md`
- `docs/MESI-mapping.md`
- `docs/threat-model.md`
- `docs/industry-context.md`
- `docs/primer-insights.md`
- `docs/depth-cascade-roadmap.md`

## Current Scope vs Next Scope

Implemented now:

- simulation prototype,
- strategy comparison,
- depth policies,
- cascade metrics,
- bounds checker.

Planned next (not yet implemented end-to-end):

- minimal TLA+ spec and TLC run integration,
- richer cascade completion semantics for consistency-directed strategies,
- tighter deterministic control for all scenarios.
