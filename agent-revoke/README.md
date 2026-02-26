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
  - `completion_semantics`
  - `delivery_completion_tick`
  - `expected_capabilities`
  - `invalidated_capabilities`
  - `cascade_completion_tick`
  - interpretation: delivery completion and local eventual invalidation completion are tracked separately
- Per-depth bound checker:
  - `unauthorised_actions(depth=d) <= f(strategy, d)`
- Heterogeneous mode:
  - role-based per-agent strategy assignment (`eager`/`lazy`/`lease`/`exec_count`)
- Adaptive mode (optional):
  - trust-driven per-agent auto-switch to stricter strategy (`adaptive_strategy` block)
- Multi-run aggregated comparison:
  - `--runs` + `--seed-start`
  - report values rendered as `mean ± std`
- Scenario schema validation:
  - `load_scenario()` validates required fields and value ranges
  - invalid configs fail fast with `ScenarioValidationError`
- Canonical scenario schema uses:
  - `simulation.num_agents`
  - `network.latency_ticks` / `network.message_loss_rate`
  - `transient.timeout_ticks`
  - `scenario.revocation_tick` / `scenario.cascade_on_revoke`
- HTML comparison report (Pico.css + Chart.js).
- Interactive React dashboard (`web/dashboard`) consuming comparison JSON exports.
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
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR
```

### 5. Generate dashboard JSON + run interactive dashboard

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --json-output /tmp/crm-dashboard.json \
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR

cd web/dashboard
npm install
npm run dev
```

Then upload `/tmp/crm-dashboard.json` in the dashboard UI.

## Judge Demo Flow (5 minutes)

### 1. CRM high-velocity scenario (main evidence)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --runs 10 \
  --seed-start 0 \
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

- Tests: `102 passed` (latest local run on **February 26, 2026**).
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
- `formal/tla/README.md`

## Current Scope vs Next Scope

Implemented now:

- simulation prototype,
- strategy comparison,
- depth policies,
- cascade metrics,
- bounds checker,
- minimal TLA+ chain model with TLC config (`formal/tla`).
- pull-strategy cascade completion semantics (`lazy`/`lease`/`exec_count`) with two-phase certificate status.
- interactive web dashboard (React) for strategy-comparison datasets.
