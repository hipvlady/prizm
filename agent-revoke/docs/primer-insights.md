# Primer Insights Applied

This project uses cache-coherence terminology as a design tool for authorisation consistency.

## Consistency Taxonomy

- `eager` aligns with consistency-agnostic coherence behaviour.
- `lazy`, `lease`, and `exec_count` align with consistency-directed behaviour.

## Temporal Coherence Analogy

- `lease` models self-invalidation by time budget.
- Security bound is time-window dependent and therefore operationally clock-sensitive.

## RCC Analogy

- `exec_count` models release/acquire-like revalidation cycles with operation budgets.
- Bound is count-based and independent of wall-clock synchronisation.

## Transient-State Accounting

- Transient states are represented explicitly in capability model.
- Timeout fail-safe enforces eventual move to `Invalid`.

## Practical Design Takeaway

The critical distinction for authorization system designers:

- time-bounded consistency (lease) is intuitive but allows large burst damage at agent velocity,
- operation-bounded consistency (`exec_count`) caps impact directly, independent of agent speed.

This maps to the OpenID Foundation's execution-count bounds concept and the CSA continuous verification pillar.
