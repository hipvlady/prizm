# Hackathon Baseline Plan v1.1 (Academic): Existing `agent-revoke` Functionality

> **Codename:** `agent-revoke-baseline`
> **Purpose:** Зафіксувати формальний baseline поточного стану системи перед впровадженням `agent-revoke-depth`.
> **Scope:** Existing revocation strategies, transient timeout fail-safe, depth metrics, comparison reporting.

---

## 1. Baseline Objective

Document and stabilise what already works today:
1. Strategy-driven revocation behaviour (`eager`, `lazy`, `lease`, `exec_count`).
2. Deterministic simulation and measurable unauthorised impact.
3. Transient-state fail-safe and convergence monitoring.
4. Report and comparison tooling suitable for demo.

---

## 2. System Snapshot (Current)

### 2.1 Core
- `Capability` includes:
  - `delegation_depth`, `parent_cap_id`
  - `max_operations`, `operations_used`
  - transient state fields
- `RevocationEvent` includes:
  - `propagated` map (`agent_id -> ack_tick|None`)
- MESI states + transient states implemented.
- Transition validation function exists.

### 2.2 Strategies
- `RevocationStrategy` ABC contract implemented by all 4 strategies:
  - `initiate_revocation`
  - `validate_action`
  - `on_tick`
  - `record_action`
  - `get_metrics`
  - `get_theoretical_bound`
  - `get_transient_state_duration`
- Strategy-level transient action policy integrated.

### 2.3 Authority / Agent
- Authority:
  - grants, delegates, revokes
  - cascade traversal via BFS
  - status API returns pending ACKs and propagation map
- Agent runtime:
  - push revocation handling
  - action validation via strategy
  - transient timeout checks

### 2.4 Simulation
- Deterministic ticks + seeded RNG
- Optional `actions_per_tick` for high-velocity deterministic runs
- Message loss support (`message_loss_rate`)
- Staleness monitoring + latency metrics
- perf_counter instrumentation (`wall_time`, per-tick timings)

### 2.5 Output
- HTML report with strategy comparison sections
- Optional `rich.live.Live` terminal view
- Comparison runner script:
  - `scripts/run_strategy_comparison.py`

---

## 3. Baseline ADRs (Current State)

### ADR-B01: Tick-Deterministic Simulation
- **Decision:** Logical tick, seeded randomness.
- **Consequence:** Reproducible strategy comparisons.

### ADR-B02: Transient Timeout Fail-Safe
- **Decision:** transient > timeout => force `Invalid`.
- **Consequence:** Prevents stuck transient liveness failures.

### ADR-B03: Strategy-Specific Revocation Semantics
- **Decision:** push revocation strictly enforced for consistency-agnostic path.
- **Consequence:** clearer behavioural separation across strategies.

### ADR-B04: BFS Cascade Traversal
- **Decision:** cascade descendants derived via BFS.
- **Consequence:** scalable, stack-safe traversal.

---

## 4. Current Invariants (Implemented)

1. `operations_used` monotonic increment.
2. Scope attenuation on delegation (`child.scope ⊆ parent.scope`).
3. Cascade traversal completeness over reachable descendants (BFS traversal).
4. Transient timeout convergence toward `Invalid`.
5. Staleness window measured from authority-invalid/local-valid mismatch.

---

## 5. Current Metrics (Available)

- `unauthorized_actions_count`
- `unauthorized_actions_by_depth`
- `revocation_latency_p50/p99`
- `staleness_window_max`
- `transient_state_timeouts`
- `convergence_time`
- `message_overhead`
- `revalidation_count`
- `wall_time_seconds`
- `avg_tick_seconds`, `p95_tick_seconds`

---

## 6. Known Baseline Gaps (Before Depth Extension)

1. No explicit `DelegationPolicy` object with `max_depth`.
2. No formal `expected_capabilities/invalidated_capabilities` cascade certificate.
3. No first-class `bound_violations_by_depth` checker.
4. No formal TLA+ artifacts in repo (`ChainRevocation.tla/.cfg`).

---

## 7. Validation Baseline

### Test Status
- Pytest suite passing (`60 passed` baseline at latest validation).

### Coverage Status
- Coverage >80% target satisfied (last measured ~91%).

### Demo Baseline
- Comparison runner produces deterministic high-velocity contrast:
  - `eager`, `lazy`, `lease`, `exec_count`
  - stable output for report generation.

---

## 8. Baseline Deliverables (Documentary)

1. Existing functionality map (this document).
2. Demo-first baseline map (paired file).
3. Migration anchor for `agent-revoke-depth` implementation planning.

---

## 9. Transition Plan to `agent-revoke-depth`

From this baseline, next steps:
1. Introduce `DelegationPolicy`.
2. Add cascade correctness certificate.
3. Add per-depth bound checker.
4. Add minimal TLA+ model for chain invariants.

---

## 10. Definition of Baseline Done

1. Baseline functionality formally documented.
2. Existing tests and metrics are stable reference point.
3. Clear delta list to depth-guarantee implementation.

