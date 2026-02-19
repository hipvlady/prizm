# MESI to Agent Authorisation Mapping

## Stable States

- `Modified` -> agent delegated further; local authority view is stale until cascade settles.
- `Exclusive` -> sole holder of delegated capability.
- `Shared` -> multiple read-capable holders.
- `Invalid` -> revoked/expired/exhausted capability.

## Transient States

- `ISG`, `IED` -> acquisition/delegation in flight; deny actions.
- `EIA`, `SIA` -> invalidation in flight; strategy-dependent allowance.
- `MIC`, `MIA` -> cascade teardown; writes denied, reads may continue.

## Protocol Mapping

- Invalidation broadcast -> revocation event broadcast.
- Snooping -> all-agent subscription in MVP.
- Directory-style scaling -> targeted broadcast by affected agent IDs.

## Invariant Highlights

- SWMR: at most one writer-level holder (`M`/`E`) at a time.
- Bounded staleness: enforced by strategy bound (time or operations).
- Fail-safe: transient timeout always converges to `Invalid`.
