# Quick Start Guide

## Project Claim

`agent-revoke` demonstrates bounded staleness in multi-agent authorization revocation using coherence-inspired strategy design.

## Why It Matters

If revocation propagation is delayed, compromised agents can continue acting. In high-velocity agentic systems this creates large security impact before convergence. Traditional TTL-based credential systems provide no velocity-aware bounds.

## What To Look For

1. Strategy trade-off is measurable -- not all strategies rank linearly.
2. Delegation depth behavior is visible through per-depth metrics.
3. Bound semantics are explicit, not implicit -- RCC provides deterministic ceilings.
4. Results are reproducible with provided commands and deterministic seeds.

## Evaluation Script (5 Minutes)

### Step 1: Run tests

```bash
pytest -q
```

Expected: all tests pass (102 tests, 88% coverage).

### Step 2: CRM comparison (core evidence)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR
```

Open report and examine unauthorized action differences:

- `lease` (time-window bound) allows large post-revoke volume.
- `exec_count` constrains impact to configured operation budget.
- Aggregated rows are reported as `mean +/- std` across seeds.

### Step 3: Banking cascade depth behavior

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/banking-cascade.yaml \
  --output /tmp/banking-comparison.html \
  --log-level ERROR
```

Open depth analysis section. Depth distribution is tracked as a first-class metric.

### Step 4: Anomaly-triggered revocation

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/anomaly-autorevoke.yaml \
  --output /tmp/anomaly-comparison.html \
  --log-level ERROR
```

## Evaluation Checklist

- [ ] Four strategies are runnable from one command
- [ ] HTML report is generated and readable offline
- [ ] Depth metrics are present in cascade analysis
- [ ] Documentation states implemented scope vs planned scope clearly
- [ ] Safety/liveness vocabulary is used consistently with system behavior

## Interpretation Notes

- CRM scenario is deterministic (`actions_per_tick=100`, fixed seed) -- sigma=0 confirms exact bounds.
- Banking and anomaly scenarios may vary with stochastic action scheduling.
- Cascade status is two-phase:
  - delivery completion (`delivery_completion_tick`) means all recipients observed revoke,
  - local completion (`cascade_completion_tick`) means all expected local capabilities invalidated.
