# Full Demo Validation Summary

Generated: 2026-02-19T21:24:17.779052

## banking-cascade

| Strategy | Unauthorized | Cascade Ratio | Bound Violations | Staleness Max |
|---|---:|---:|---:|---:|
| eager | 17 | 1.00 | 0 | 10 |
| lazy | 33 | 1.00 | 0 | 23 |
| lease | 30 | 1.00 | 0 | 20 |
| exec_count | 13 | 1.00 | 0 | 12 |

## crm-bulk-ops

| Strategy | Unauthorized | Cascade Ratio | Bound Violations | Staleness Max |
|---|---:|---:|---:|---:|
| eager | 500 | 1.00 | 0 | 5 |
| lazy | 2400 | 1.00 | 0 | 24 |
| lease | 6000 | 1.00 | 0 | 60 |
| exec_count | 50 | 1.00 | 0 | 0 |

## anomaly-autorevoke

| Strategy | Unauthorized | Cascade Ratio | Bound Violations | Staleness Max |
|---|---:|---:|---:|---:|
| eager | 108 | 1.00 | 0 | 10 |
| lazy | 12 | 1.00 | 0 | 2 |
| lease | 2952 | 0.00 | 0 | 246 |
| exec_count | 19 | 1.00 | 0 | 2 |

## Validation Checks

- PASS: `banking_eager_vs_lazy_diff`
- PASS: `banking_all_bound_violations_zero`
- PASS: `crm_all_cascade_ratio_one`
- PASS: `anomaly_nonzero_signal_exists`
- PASS: `anomaly_lease_expected_nonconvergence`
