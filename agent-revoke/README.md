# agent-revoke

Temporal consistency simulator for multi-agent authorization revocation, modeled after MESI coherence concepts and consistency-directed strategies.

## Stack

- Python 3.11+
- `dataclasses` + `Enum`
- `pytest`
- `rich`
- `jinja2`
- `pyyaml`

## Install

```bash
pip install -r requirements.txt
```

## Run Tests

```bash
pytest -q
```

## Run Simulation

```bash
python -m src.simulation.engine scenarios/banking-cascade.yaml --strategy eager
python -m src.simulation.engine scenarios/crm-bulk-ops.yaml --strategy exec_count
python -m src.simulation.engine scenarios/anomaly-autorevoke.yaml --strategy lazy
```

## Run Strategy Comparison Report

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output crm-comparison.html
```

## Key Concepts Implemented

- PDP/PEP separation via revocation events
- Logical tick-based simulation clock
- Four pluggable strategies: `eager`, `lazy`, `lease`, `exec_count`
- BFS cascade traversal for delegation chains
- ADR-005 transient-state timeout fail-safe to `Invalid`
- Unauthorized action metrics including per-depth breakdown
