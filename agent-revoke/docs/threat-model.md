# Threat Model

## Scenario 1: Banking Cascade Delay

- Root capability revoked in a delegation chain.
- Risk: downstream agent continues acting during propagation window.
- Control: eager invalidation or short bounded strategy with cascade metrics by depth.

## Scenario 2: High-Velocity CRM Agent

- Credential compromise under heavy action rate.
- Risk: large unauthorized operation volume before revocation converges.
- Control: exec-count bounded credentials to cap impact deterministically.

## Scenario 3: Behavioural Anomaly

- Agent behaviour shifts (timing/bulk pattern).
- Risk: delayed human response to compromised automation.
- Control: trust scorer anomaly trigger with automatic revocation.
