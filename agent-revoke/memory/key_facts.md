# Key Facts & Invariants

## Stack

- Python 3.11+, dataclasses (frozen=True where immutable), Enum, ABC, match/case
- Terminal UI: rich library (rich.live.Live for real-time MESI state updates)
- HTML report: Jinja2 templates, embedded Chart.js from CDN
- No ORM, no async framework — pure simulation, dict[UUID, ...] registries

## Time Budget

| Step | Estimate |
|------|----------|
| Step 1 | 1.5h |
| Step 2 | 2.0h |
| Step 3 | 1.5h |
| Step 4 | 2.0h |
| Step 5 | 2.0h |
| Step 6 | 1.0h |
| **Total** | **~10h** |

## Killer Metrics

- TTL(60s) @ 100ops/sec -> up to 6000 unauthorized ops vs exec-count(50) -> exactly 50
- anomaly_threshold = 0.3 (trust score floor for auto-revocation)

## Important Defaults

- max_operations=None means unbounded (NOT zero)
