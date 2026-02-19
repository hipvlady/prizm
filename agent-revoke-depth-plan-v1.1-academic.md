# Hackathon Project Plan v1.1 (Academic): Delegation Depth Coherence and Cascade Guarantees

> **Codename:** `agent-revoke-depth`
> **Track:** Formal methods + security systems
> **Objective:** Підсилити `agent-revoke` формальними гарантіями для delegation chains: policy safety, cascade correctness, bounded unauthorized impact by depth.

---

## 1. Problem Statement

У multi-agent delegation chains ревокація має бути:
1. **Policy-correct** під час делегації (`max_depth`, scope attenuation, remaining ops propagation).
2. **Cascade-complete** після revoke(root): всі нащадки мають досягнути стабільного `Invalid`.
3. **Bounded**: кількість unauthorized operations на глибині `d` не перевищує `f(strategy, d)`.

Гіпотеза: для operation-bounded strategy (exec-count) bound є детермінованим і не залежить від velocity.

---

## 2. Formal Model (Minimal)

### 2.1 System

Define CCS-Depth as:

```text
S = <A, C, parent, depth, state, scope, opsMax, opsUsed, strategy, event>
```

where:
- `A` agents
- `C` capabilities
- `parent: C -> C ∪ {None}`
- `depth: C -> Nat`
- `state: C -> {M,E,S,I} ∪ Transient`
- `scope: C -> P(Permissions)`
- `opsMax, opsUsed: C -> Nat`

### 2.2 Delegation Policy Constraints

For child capability `c'` delegated from parent `c`:

1. `depth(c') = depth(c) + 1`
2. `depth(c') <= max_depth`
3. `scope(c') ⊆ scope(c)`
4. `opsMax(c') <= opsMax(c) - opsUsed(c)` if bounded

### 2.3 Cascade Correctness

Let `Desc(root)` be BFS descendants in delegation DAG.
For revocation event `e(root)`:

1. `expected(e) = Desc(root) ∪ {root}`
2. `invalidated(e, t) ⊆ expected(e)`
3. Completion at time `t*` iff `invalidated(e, t*) = expected(e)` and all are stable `I`.

---

## 3. Proof Obligations (TLA+ Target)

### PO-1 Safety

```text
RevokedParentImpliesEventuallyInvalidDescendants
```

If root is revoked, no descendant remains permanently valid.

### PO-2 Liveness

```text
NoStuckTransient
```

Any capability in transient state older than timeout transitions to `I`.

### PO-3 Bound

```text
DepthBoundHolds
```

For each depth `d`:

```text
unauthByDepth[d] <= F(strategy, d)
```

---

## 4. Bound Function

Use operational upper bound for hackathon evaluation:

```text
F(eager, d)      = v(d) * net_latency * (d+1)
F(lazy, d)       = v(d) * (check_interval + net_latency * (d+1))
F(lease, d)      = v(d) * ttl
F(exec_count, d) = remaining_ops_at_revoke(d)
```

Primary theorem candidate:

```text
For exec_count, unauthByDepth[d] <= remaining_ops_at_revoke(d), independent of v(d).
```

---

## 5. Architecture Changes

### 5.1 Domain
- `DelegationPolicy(max_depth, require_scope_subset, propagate_remaining_ops)`
- `RevocationEvent.expected_capabilities`
- `RevocationEvent.invalidated_capabilities`
- `RevocationEvent.propagated` (ack tick map)

### 5.2 Services
- `AuthorityService.validate_delegation_depth(...)`
- `AuthorityService.get_cascade_status(event_id)`
- `ConsistencyMonitor.register_expected_cascade(...)`
- `ConsistencyMonitor.mark_capability_invalidated(...)`
- `ConsistencyMonitor.get_cascade_completeness_ratio(...)`

### 5.3 Metrics
- `cascade_completeness_ratio`
- `cascade_completion_tick`
- `bound_violations_by_depth`
- `unauthorized_actions_by_depth` (already present, extended checks)

---

## 6. TLA+ Spec Layout

### Files
- `formal/ChainRevocation.tla`
- `formal/ChainRevocation.cfg`
- `formal/README.md`

### Variables
- `capState`
- `parent`
- `depth`
- `opsRemaining`
- `expected`
- `invalidated`
- `unauthByDepth`
- `transientAge`

### Actions
- `Delegate`
- `RevokeRoot`
- `Propagate`
- `TimeoutFailSafe`
- `AttemptAction`

### Model bounds
- `NumCaps <= 8`
- `MaxDepth <= 3`
- finite operation budgets

---

## 7. Experimental Protocol

### Scenarios
1. `banking-depth-guarantee.yaml` (depth 3-4 chain)
2. `crm-bulk-ops.yaml` (high velocity baseline with depth=1)

### Runs
- 10 seeds per strategy
- deterministic tick engine

### Reported Statistics
- mean, sigma
- p50/p99 cascade completion ticks
- bound violation count by depth

---

## 8. Implementation Timeline (~10h)

1. **1.5h** Policy gate implementation + tests
2. **2.0h** Cascade certificate state + monitor API
3. **2.0h** Bound checker + report additions
4. **2.5h** TLA+ minimal model + TLC runs
5. **1.0h** Integration validation + narrative polishing
6. **1.0h** Buffer for bugfixes

---

## 9. Risks and Mitigations

1. **Depth convention mismatch**
- Fix: hardcode `root=0`, assert everywhere.

2. **False completion (ACK != stable invalid)**
- Fix: completion requires stable `I` for all expected capabilities.

3. **Off-by-one in remaining ops**
- Fix: boundary-focused tests and property tests.

4. **TLC blow-up**
- Fix: bounded model + minimal state space.

---

## 10. Deliverables

### Code
- Delegation depth policy enforcement
- Cascade completeness certificate
- Depth-bound checker and violations counter

### Formal
- TLA+ spec + cfg + reproducible TLC output

### Documentation
- Bound definitions
- Invariant mapping (code <-> TLA+)
- Repro steps

---

## 11. Success Criteria

Must-have:
1. All tests green.
2. TLC invariants pass.
3. No bound violations in reference runs.
4. Demonstrable 100% cascade completeness for BFS expected set.

Should-have:
1. Side-by-side strategy report with per-depth bounds.
2. Deterministic replay script.

