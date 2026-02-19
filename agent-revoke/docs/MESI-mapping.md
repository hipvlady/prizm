# MESI to Agent Authorisation Mapping

## Stable States

| MESI State | Capability Meaning | Security Interpretation |
|---|---|---|
| `Modified` | Delegated further; local owner has dirty authority view | Chain extension in progress may require cascade invalidation |
| `Exclusive` | Single valid holder | Sole actor currently authorised |
| `Shared` | Multiple read-capable holders | Parallel limited access |
| `Invalid` | Revoked / expired / exhausted | Authorisation denied |

## Transient States

| State | Transition Intent | Action Handling |
|---|---|---|
| `ISG` | Invalid -> Shared (await grant) | deny |
| `IED` | Invalid -> Exclusive (await delegation setup) | deny |
| `EIA` | Exclusive -> Invalid (await acknowledgement) | strategy-dependent |
| `SIA` | Shared -> Invalid (await acknowledgement) | strategy-dependent |
| `MIC` | Modified -> Invalid (await cascade completion) | restrictive |
| `MIA` | Modified -> Invalid (await delegator acknowledgement) | restrictive |

Transient timeout fail-safe (ADR-005): unresolved transient state moves to `Invalid` after configured timeout.

## Protocol-Level Analogy

- Invalidation broadcast -> revocation event broadcast.
- Snooping topology -> all-agent subscription in MVP.
- Directory-style targeting -> recipient-filtered propagation map.

## Coherence Class Mapping

- Consistency-agnostic: `eager`
- Consistency-directed: `lazy`, `lease`, `exec_count`

## Practical Security Meaning

The mapping provides a concrete mental model for stale-credential behaviour:

- stale reads/writes correspond to stale local capability states,
- invalidation strategy determines security window,
- measured unauthorised operations quantify damage during coherence lag.
