# Minimal TLA+ Pack

This folder contains the smallest formal model used in the roadmap wave:

- `RevocationChain.tla`: chain revocation model with timeout and depth-bound counters.
- `RevocationChain.cfg`: TLC model configuration for a 3-hop delegation chain.

## Checked properties

- `CascadeSafety`: revoked ancestor implies descendants eventually reach `Invalid`.
- `TransientEventuallyInvalid`: transient states eventually resolve to `Invalid`.
- `TransientAgeBound`: no capability remains transient at or above timeout.
- `UnauthorizedWithinBound`: unauthorized actions by depth stay under configured bounds.

## Run with TLC

1. Download `tla2tools.jar` from the official TLA+ release.
2. Run TLC from the project root:

```bash
java -cp /path/to/tla2tools.jar tlc2.TLC \
  -workers auto \
  -cleanup \
  -config formal/tla/RevocationChain.cfg \
  formal/tla/RevocationChain.tla
```

Expected result for the provided model: all invariants and properties pass.
