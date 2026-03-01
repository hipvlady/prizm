# Metrics and Evidence

## How To Reproduce

### Tests

```bash
pytest -q
```

### Coverage

```bash
coverage run -m pytest -q
coverage report -m
```

Latest local run:

- tests: `102 passed` (**February 26, 2026**)
- total line coverage: `88%`

### Strategy comparison

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR
```

## Canonical Scenario Metrics

The most deterministic benchmark is `crm-bulk-ops.yaml` (`agent_velocity=100`, seed 42, revoke at tick 0).

Sample output captured on **19 February 2026**:

| Strategy | Unauthorised Ops | Staleness Max (ticks) | P50 Revocation Latency (ticks) |
|---|---:|---:|---:|
| eager | 500 | 5 | 5.0 |
| lazy | 2400 | 24 | 0.0 |
| lease | 6000 | 60 | 0.0 |
| exec_count | 50 | 0 | 0.0 |

Interpretation:

- `lease` bound scales with TTL window.
- `exec_count` bound is deterministic and operation-limited.
- `eager` minimises staleness but still has in-flight impact under configured network latency.

## Banking Cascade Snapshot

Scenario: `banking-cascade.yaml` (seed 42, 10 agents, depth 3, revoke at tick 100).

Sample output captured on **19 February 2026**:

| Strategy | Unauthorized Ops | Cascade Ratio | Staleness Max |
|---|---:|---:|---:|
| eager | 17 | 1.00 | 10 |
| lazy | 33 | 1.00 | 23 |
| lease | 30 | 1.00 | 20 |
| exec_count | 13 | 1.00 | 12 |

Note: this scenario uses stochastic action scheduling (`action_probability=0.5`), so absolute values may vary across seeds.

## Bound-Checker Status

Per-depth bound checking is implemented in `src/simulation/bounds.py` and invoked from the simulation engine.

Current tested guarantee:

- `tests/test_step5.py::test_reference_configs_have_no_bound_violations`
- verifies zero bound violations for all four strategies in the CRM reference scenario.

## Output Artefacts

- HTML comparison reports from script output path.
- Strategy summary on stdout.
- Optional aggregated report mode (`--runs > 1`) with `mean ± std`.
- Structured logs with severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
