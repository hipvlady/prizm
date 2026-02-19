# Demo Artifacts: Full Scenario Run (2026-02-19)

This folder contains outputs from running the full demo suite:

1. `banking-cascade.yaml`
2. `crm-bulk-ops.yaml`
3. `anomaly-autorevoke.yaml`

Each scenario was run with all four strategies via `scripts/run_strategy_comparison.py`:

- `eager`
- `lazy`
- `lease`
- `exec_count`

## Contents

- `reports/` HTML comparison reports (one per scenario)
- `logs/` command stdout logs (one per scenario)
- `summary.json` machine-readable aggregate metrics
- `SUMMARY.md` human-readable table summary
