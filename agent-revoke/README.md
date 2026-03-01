# agent-revoke

Temporal consistency simulator for multi-agent authorization revocation, inspired by MESI coherence and consistency-directed protocols.

## Overview

`agent-revoke` compares four revocation strategies (`eager`, `lazy`, `lease`, `exec_count`) under repeatable scenarios. It measures:

- unauthorized actions (total and per delegation depth)
- staleness window duration
- revocation latency (p50/p99)
- cascade behavior by delegation depth
- clock-dependence profile (time-bounded vs operation-bounded)

The simulator implements the Capability Coherence System (CCS) framework described in the accompanying paper.

## What Is Implemented

- Python 3.11+ simulator with typed domain model (`dataclasses` + `Enum`)
- PDP/PEP split:
  - `AuthorityService` (policy decision point)
  - `AgentRuntime` (policy enforcement point)
- Four pluggable strategies:
  - `eager` (consistency-agnostic, SWMR-like push invalidation)
  - `lazy` (consistency-directed, periodic check interval)
  - `lease` (time-bound, clock-dependent TTL self-invalidation)
  - `exec_count` (operation-bound, clock-independent RCC semantics)
- Delegation policy controls:
  - `max_depth` enforcement
  - scope attenuation enforcement
  - remaining operation propagation
- BFS cascade traversal with cascade certificate fields:
  - `completion_semantics`
  - `delivery_completion_tick` / `cascade_completion_tick`
  - `expected_capabilities` / `invalidated_capabilities`
- Per-depth bound checker:
  - `unauthorized_actions(depth=d) <= f(strategy, d)`
- Heterogeneous mode:
  - role-based per-agent strategy assignment
- Adaptive mode:
  - trust-driven per-agent auto-switch to stricter strategy
- Multi-run aggregated comparison:
  - `--runs` + `--seed-start`, values reported as `mean +/- std`
- Scenario schema validation:
  - `load_scenario()` validates required fields and value ranges
  - invalid configs fail fast with `ScenarioValidationError`
- HTML comparison report (Pico.css + Chart.js)
- Interactive React dashboard (`web/dashboard`) consuming comparison JSON exports
- Minimal TLA+ formal model (`formal/tla/`) with safety, liveness, and bound invariants
- Automated tests and coverage (102 tests, 88% coverage)

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

## Evaluation Walkthrough

### 1. CRM high-velocity scenario (core evidence)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR
```

Open `/tmp/crm-comparison.html`. This scenario is fully deterministic (`actions_per_tick=100`).

Reference output:

| Strategy | Unauthorized | Staleness Max |
|---|---:|---:|
| eager | 500 | 5 |
| lazy | 2,400 | 24 |
| lease | 6,000 | 60 |
| exec_count | 50 | 0 |

### 2. Banking cascade scenario (depth propagation)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/banking-cascade.yaml \
  --output /tmp/banking-comparison.html \
  --log-level ERROR
```

Open `/tmp/banking-comparison.html` and inspect the per-depth analysis section.

### 3. Anomaly auto-revocation scenario

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/anomaly-autorevoke.yaml \
  --output /tmp/anomaly-comparison.html \
  --log-level ERROR
```

## Quality Signals

- Tests: `102 passed`
- Coverage: `88%` (`coverage run -m pytest && coverage report -m`)
- Exceptions are domain-specific (`RevocationError`, `StaleCredentialError`, `CacheMissError`, etc.)
- Structured logging with severity levels (`DEBUG`/`INFO`/`WARNING`/`ERROR`)
- Latency instrumentation uses `time.perf_counter()`

## Documentation

- [`docs/README.md`](docs/README.md) -- documentation index
- [`docs/architecture-and-invariants.md`](docs/architecture-and-invariants.md) -- system design and guarantees
- [`docs/MESI-mapping.md`](docs/MESI-mapping.md) -- MESI-to-authorization state mapping
- [`docs/industry-context.md`](docs/industry-context.md) -- CSA, OpenID, OpenFGA/Oso alignment
- [`docs/agentic-iam-code-mapping.md`](docs/agentic-iam-code-mapping.md) -- standards concepts mapped to code paths
- [`docs/threat-model.md`](docs/threat-model.md) -- attack windows and controls
- [`docs/metrics-and-evidence.md`](docs/metrics-and-evidence.md) -- reproducible commands and observed results
- [`docs/quick-start-guide.md`](docs/quick-start-guide.md) -- step-by-step evaluation walkthrough
- [`docs/scenario-schema.md`](docs/scenario-schema.md) -- scenario YAML contract
- [`docs/temporal-logic-invariants.md`](docs/temporal-logic-invariants.md) -- CTL/LTL formulas and implementation mapping
- [`formal/tla/README.md`](formal/tla/README.md) -- TLA+ model and TLC instructions
- [`web/dashboard/README.md`](web/dashboard/README.md) -- React dashboard

## Roadmap

Implemented now:

- simulation prototype with four strategies
- strategy comparison with multi-run statistics
- delegation depth policies with cascade metrics
- bounds checker with per-depth violation tracking
- minimal TLA+ chain model with TLC verification
- pull-strategy cascade completion semantics with two-phase certificate status
- interactive web dashboard for strategy-comparison datasets
- heterogeneous and adaptive strategy modes

Planned:

- Broader TLA+ model covering multi-agent interference
- Shared Signals Framework / OIDC-A protocol integration
- Scale evaluation to 50-100 agents
- Byzantine fault injection
- Replicated authority service for partition resilience
