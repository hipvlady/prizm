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

- tests: `72 passed`
- total line coverage: `88%`

### Strategy comparison

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --log-level ERROR
```

## Canonical Scenario Metrics

The most deterministic benchmark is `crm-bulk-ops.yaml` (`actions_per_tick=100`, fixed seed).

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

Scenario: `banking-cascade.yaml`.

Sample output captured on **19 February 2026**:

- `eager`: unauthorised `17`, staleness max `10`
- `lazy`: unauthorised `17`, staleness max `10`
- `lease`: unauthorised `136`, staleness max `99`
- `exec_count`: unauthorised `129`, staleness max `99`

Note: this scenario is stochastic (no fixed seed in YAML), so absolute values may vary between runs.

## Bound-Checker Status

Per-depth bound checking is implemented in `src/simulation/bounds.py` and invoked from the simulation engine.

Current tested guarantee:

- `tests/test_step5.py::test_reference_configs_have_no_bound_violations`
- verifies zero bound violations for all four strategies in the CRM reference scenario.

## Output Artefacts

- HTML comparison reports from script output path.
- Strategy summary on stdout.
- Structured logs with severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
