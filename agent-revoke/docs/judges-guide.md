# Judges Guide

## Project Claim

`agent-revoke` demonstrates bounded staleness in multi-agent authorisation revocation using coherence-inspired strategy design.

## Why It Matters

If revocation propagation is delayed, compromised agents can continue acting. In high-velocity systems this creates large security impact before convergence.

## What To Look For In Demo

1. Strategy trade-off is measurable.
2. Delegation depth behaviour is visible.
3. Bound semantics are explicit, not implicit.
4. Results are reproducible with provided commands.

## Demo Script (5 Minutes)

### Step 1: Run tests

```bash
pytest -q
```

Expected: all tests pass.

### Step 2: Show CRM comparison (core signal)

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/crm-bulk-ops.yaml \
  --output /tmp/crm-comparison.html \
  --runs 10 \
  --seed-start 0 \
  --log-level ERROR
```

Open report and highlight unauthorised action differences:

- `lease` (time-window bound) allows large post-revoke volume.
- `exec_count` constrains impact to configured operation budget.
- Aggregated rows are reported as `mean ± std` across seeds.

### Step 3: Show cascade depth behaviour

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/banking-cascade.yaml \
  --output /tmp/banking-comparison.html \
  --log-level ERROR
```

Open depth analysis section. Explain that depth distribution is tracked as a first-class metric.

### Step 4: Show anomaly-triggered revocation path

```bash
python scripts/run_strategy_comparison.py \
  --scenario scenarios/anomaly-autorevoke.yaml \
  --output /tmp/anomaly-comparison.html \
  --log-level ERROR
```

## Judge Checklist

- [ ] Four strategies are runnable from one command.
- [ ] HTML report is generated and readable offline.
- [ ] Depth metrics are present.
- [ ] Documentation states implemented scope vs planned scope clearly.
- [ ] Safety/liveness vocabulary is used consistently with system behaviour.

## Fair Interpretation Notes

- CRM scenario is deterministic (`actions_per_tick=100`, fixed seed).
- Banking and anomaly scenarios may vary with stochastic action scheduling.
- Cascade status is two-phase:
  - delivery completion (`delivery_completion_tick`) means all recipients observed revoke,
  - local completion (`cascade_completion_tick`) means all expected local capabilities invalidated.
