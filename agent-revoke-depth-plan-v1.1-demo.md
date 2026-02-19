# Hackathon Project Plan v1.1 (Demo-First): Delegation Depth and Cascade Guarantees

> **Codename:** `agent-revoke-depth`
> **Format:** Solo, ~10 hours
> **Pitch line:** *“Compromised root agent revoked now. We can prove the chain converges and bound the damage per depth.”*

---

## 1. Demo Story (What Judges Will See)

### 1.1 Core Message
1. Delegation is not infinite: policy enforces `max_depth`.
2. Revocation is not “best effort”: BFS cascade has measurable completeness.
3. Damage is not unknown: per-depth unauthorized ops are bounded by strategy.

### 1.2 5-Minute Flow
1. **Depth gate:** show `depth=4` delegation denied by policy.
2. **Root compromise:** trigger root revoke on chain A→B→C→D.
3. **Live convergence:** expected descendants vs invalidated progress.
4. **Per-depth bound chart:** eager/lazy/lease/exec-count comparison.
5. **Formal trust stamp:** TLA+ invariants pass on bounded model.

---

## 2. Build Scope (Hackathon-Optimal)

### 2.1 Must Build
1. **Delegation depth policies**
- `max_depth`
- scope attenuation check
- remaining_ops propagation check

2. **Cascade correctness guarantees**
- BFS expected set
- invalidated set tracking
- completion ratio + completion tick
- per-depth bound checker

3. **Minimal TLA+**
- Safety
- Liveness
- Bound

### 2.2 Nice-to-Have
- Rich live panel for expected/invalidated counters
- One-click command: run scenarios + generate HTML + show TLA result

---

## 3. Implementation Blueprint

## 3.1 Data and Status Model

```python
DelegationPolicy:
  max_depth: int
  require_scope_subset: bool
  propagate_remaining_ops: bool

RevocationEvent:
  root_capability_id: UUID
  expected_capabilities: set[UUID]
  invalidated_capabilities: set[UUID]
  propagated: dict[agent_id -> ack_tick]
```

### 3.2 Service API
- `AuthorityService.set_delegation_policy(policy)`
- `AuthorityService.delegate_capability(...)` policy-enforced
- `AuthorityService.get_cascade_status(event_id)`:
  - expected
  - invalidated
  - ratio
  - pending
  - completion_tick

### 3.3 Monitor API
- `register_expected_cascade(event_id, expected_set)`
- `mark_capability_invalidated(event_id, cap_id, tick)`
- `get_cascade_completeness_ratio(event_id)`

---

## 4. Bound Checker

For each depth `d`:

```text
unauthorized_ops[d] <= F(strategy, d)
```

MVP formulas:
- eager: `v(d) * net_latency * (d+1)`
- lazy: `v(d) * (check_interval + net_latency * (d+1))`
- lease: `v(d) * ttl`
- exec_count: `remaining_ops_at_revoke(d)`

Output:
- `bound_violations_by_depth: {d: count}`

---

## 5. Minimal TLA+ (Judge-Friendly)

### 5.1 Files
- `formal/ChainRevocation.tla`
- `formal/ChainRevocation.cfg`
- `formal/README.md`

### 5.2 Invariants to show on slide
1. **Safety**
- revoked parent => descendants eventually invalid
2. **Liveness**
- no transient state stuck past timeout
3. **Bound**
- unauthorised ops at depth d never exceed strategy bound

### 5.3 Practical Model Limits
- depth up to 3
- small finite chain
- deterministic transitions

---

## 6. Scenario Pack

### 6.1 New scenario
`scenarios/banking-depth-guarantee.yaml`

Recommended config:
- chain depth: 4
- revoke tick: deterministic (e.g. 20)
- transient timeout: explicit
- run all four strategies

### 6.2 Existing scenarios reuse
- `crm-bulk-ops` for high-velocity bound contrast
- optional `anomaly-autorevoke` as secondary story

---

## 7. Output Pack

### 7.1 Terminal
- show:
  - current tick
  - cascade ratio
  - pending descendants
  - violations by depth

### 7.2 HTML report additions
1. Cascade completeness card
2. Expected vs invalidated table
3. Per-depth unauthorized vs bound table
4. Pass/fail flag for bound checks

---

## 8. Testing Checklist

### 8.1 Unit
- depth overflow denied
- exact max depth allowed
- child scope broader than parent denied
- child max_ops > parent remaining denied

### 8.2 Integration
- BFS expected set matches graph descendants
- completion ratio reaches `1.0`
- completion only when all are stable invalid
- bound checker catches synthetic violation

### 8.3 Formal
- TLC passes all three invariants on bounded model

---

## 9. Timeline (~10h)

1. **1.5h** policy enforcement + domain errors
2. **2.0h** cascade certificate + monitor status API
3. **2.0h** bound checker + metrics + report table
4. **2.0h** TLA+ minimal model + TLC run
5. **1.5h** demo scenario wiring + terminal polish
6. **1.0h** tests, bugfix, dry-run presentation

---

## 10. Risks (Demo Lens)

1. **Off-by-one in remaining_ops**
- mitigation: boundary tests first

2. **Depth mismatch root=0/1**
- mitigation: enforce root=0 in code and scenario docs

3. **False cascade complete**
- mitigation: require stable Invalid for all expected caps

4. **TLA setup delay**
- mitigation: prepare TLC command + tiny model first

---

## 11. Final Demo Script (Exact Words Template)

1. “We enforce bounded delegation at creation time.”
2. “Now root is compromised; revoke triggered.”
3. “This is expected cascade set, this is invalidated set, ratio grows to 100%.”
4. “Here are unauthorized ops per depth and strategy bounds.”
5. “TLA+ confirms safety, liveness, and bound invariants on bounded model.”

---

## 12. Definition of Done

1. All tests pass.
2. Scenario produces non-empty cascade completeness and depth-bound metrics.
3. No bound violations in reference baseline runs.
4. TLC invariants pass.
5. Report and terminal output are demo-ready.

