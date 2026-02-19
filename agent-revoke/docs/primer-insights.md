# Primer Insights Applied

## Consistency Classes

- `eager` maps to consistency-agnostic coherence.
- `lazy`, `lease`, `exec_count` map to consistency-directed coherence.

## Temporal Coherence

- Lease strategy models lease-based self-invalidation.
- Bound is explicit in ticks and depends on clock alignment.

## RCC Analogy

- Exec-count strategy models operation-bounded release/acquire cycles.
- Bound is operation-count based, independent of wall-clock synchronisation.

## Transient Handling

- Transient states are first-class and included in staleness analysis.
- ADR-005 timeout enforces liveness even under dropped messages.
