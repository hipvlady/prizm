# Hackathon Baseline Plan v1.1 (Demo-First): Existing `agent-revoke` Functionality

> **Codename:** `agent-revoke-baseline`
> **Pitch line:** *“Ми вже маємо працюючий revocation simulator з 4 стратегіями, depth metrics і reproducible comparison.”*

---

## 1. What Is Already Demo-Ready

1. 4 revocation strategies працюють у спільному simulation engine.
2. Є deterministic comparison runner для сценарію.
3. Є depth-aware unauthorized metrics.
4. Є HTML report і optional live terminal view.
5. Є passing test suite + high coverage.

---

## 2. 5-Minute Baseline Demo (Current System)

1. Запускаємо comparison на CRM high-velocity scenario.
2. Показуємо різницю між `lease` і `exec_count`.
3. Показуємо `unauthorized_actions_by_depth`.
4. Показуємо latency/convergence/message overhead.
5. Фіксуємо baseline: що є зараз, що додаємо next.

---

## 3. Baseline Capabilities (Current)

### 3.1 Core
- Capability model with delegation metadata.
- Revocation events with ACK timestamp map (`propagated`).
- MESI + transient states.

### 3.2 Engine
- tick-based deterministic loop
- seeded random
- actions-per-tick mode
- message loss simulation
- perf instrumentation

### 3.3 Security Logic
- scope attenuation checks
- transient timeout fail-safe
- stale credential detection
- strategy-specific transient action policy

### 3.4 Output
- HTML strategy comparison
- per-depth counts
- rich-based live panel support

---

## 4. Current Gaps (Why `agent-revoke-depth` Next)

1. Немає policy object для `max_depth`.
2. Немає machine-checkable cascade certificate:
   - expected descendants set
   - invalidated completion set
3. Немає first-class per-depth bound violation checker.
4. Немає formal TLA+ artifacts для chain invariants.

---

## 5. Baseline Metrics We Already Have

- unauthorized actions (total + by depth)
- revocation latency p50/p99
- staleness window max
- transient timeouts
- convergence time
- message overhead
- revalidation count
- wall-clock runtime + per-tick timings

---

## 6. Baseline Quality

1. Tests: passing.
2. Coverage: above required threshold.
3. Comparison pipeline: reproducible.

---

## 7. Handover to Next Scope

### From Baseline -> Depth Guarantees

1. Add `DelegationPolicy(max_depth, remaining_ops propagation)`.
2. Add cascade completeness certificate and status API.
3. Add per-depth bound checker (`bound_violations_by_depth`).
4. Add minimal TLA+ package (`Safety`, `Liveness`, `Bound`).

---

## 8. Demo Bridge Narrative (Current -> Next)

“Зараз ми можемо вимірювати impact після revoke. Наступний крок — гарантувати policy-safe delegation depth, машинно перевіряти cascade completion, і формально підтвердити chain invariants через TLA+.”

---

## 9. Definition of Baseline Ready

1. Existing functionality documented for judges and team.
2. Stable reference before feature extension.
3. Clear implementation delta for `agent-revoke-depth`.

