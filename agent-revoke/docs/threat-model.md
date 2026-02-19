# Threat Model

## Threat 1: Banking Cascade Delay

- Trigger: root capability in a delegation chain is revoked.
- Risk: downstream delegees keep acting before local cache invalidation.
- Controls implemented:
  - BFS cascade traversal,
  - strategy comparison under controlled latency,
  - per-depth unauthorised tracking.
- Residual risk:
  - consistency-directed strategies depend on check cadence/TTL/ops budget.

## Threat 2: High-Velocity Credential Compromise

- Trigger: compromised CRM sync agent continues high-rate actions.
- Risk: very large post-revoke volume in short time.
- Controls implemented:
  - deterministic high-velocity scenario,
  - operation-count strategy (`exec_count`) with strict cap,
  - bound checker with per-depth support.

## Threat 3: Behavioural Anomaly Window

- Trigger: agent behaviour deviates (timing/volume patterns).
- Risk: delayed manual response.
- Controls implemented:
  - trust scorer anomaly checks,
  - automatic revoke trigger path.
- Residual risk:
  - anomaly scenario remains a simulation approximation.

## Security Posture Summary

The prototype is strongest at demonstrating measurable revocation-window impact and strategy trade-offs. It is not a production IAM system.
