# Hackathon Project Plan: Delegation Depth Coherence and Cascade Guarantees

> **Codename:** `agent-revoke-depth`
> **Format:** Solo, ~10 hours focused implementation
> **Concept:** Розширення поточного `agent-revoke` демо фокусом на correctness delegation chains: depth-limited delegation policies, гарантована cascade revocation completeness, та мінімальна формалізація в TLA+ для chain invariants (Safety, Liveness, Bound).
> **Why now:** Це пряме продовження існуючого демо (revocation propagation + depth metrics), дає сильний security narrative ("root revoke => guaranteed cascade bound"), реально встигається у hackathon scope, та підкріплюється lightweight formal model без повного compositionality proof.

---

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Language** | Python 3.11+ | Existing codebase compatibility, typed dataclasses |
| **Modeling** | dataclasses + Enum | Deterministic domain state transitions |
| **Simulation** | Tick-based engine | Reproducible, deterministic comparisons |
| **Testing** | pytest | Fast invariant and regression checks |
| **Terminal UI** | rich (+ optional rich.live.Live) | Demonstrable cascade convergence |
| **Report** | Jinja2 + Pico.css | Static summary for judges |
| **Formal spec** | TLA+ (TLC) | Bounded model checking for chain invariants |

**Key dependencies (existing + optional formal tooling):**
```txt
rich>=13.0
jinja2>=3.1
pyyaml>=6.0
pytest>=7.0
# Optional local tool: tlc2.jar / tla2tools.jar
```

---

## Architecture Decision Records

### ADR-D01: Depth-Limited Delegation Policy
- **Status:** Accepted
- **Decision:** Delegation allowed only when `child.delegation_depth <= max_depth`.
- **Rationale:** Bounded delegation prevents untrusted long chains and contains blast radius.
- **Consequence:** `AuthorityService.delegate_capability` must reject overflow early with explicit error.

### ADR-D02: Remaining Operations Propagation
- **Status:** Accepted
- **Decision:** `child.max_operations` must not exceed `parent.remaining_operations` at delegation time.
- **Rationale:** Preserves operation-bounded damage guarantees along delegation chain.
- **Consequence:** Parent state at delegation tick becomes part of policy correctness.

### ADR-D03: Cascade Completeness Certificate (BFS)
- **Status:** Accepted
- **Decision:** On root revoke, authority computes BFS `expected_capabilities` set and tracks completion against it.
- **Rationale:** Message delivery alone does not prove correctness; we need verifiable completion evidence.
- **Consequence:** Revocation event/status must expose expected vs invalidated progress.

### ADR-D04: Minimal TLA+ Scope
- **Status:** Accepted
- **Decision:** TLA+ covers chain revocation invariants only (Safety/Liveness/Bound), not full multi-agent interference.
- **Rationale:** Maximises value within hackathon time while still adding formal credibility.
- **Consequence:** Small finite model, deterministic assumptions, explicit non-goals.

---

## Known Risks

### RISK-D01: Off-by-One in Remaining Ops Propagation
- **Context:** `remaining_ops = max_ops - operations_used`.
- **Risk:** Incorrect boundary allows child to exceed parent's residual budget.
- **Mitigation:** Unit tests at boundaries (`used==max`, `used==max-1`, `child==remaining`).

### RISK-D02: Depth Convention Drift
- **Context:** Some parts may treat root as depth `0`, others as `1`.
- **Risk:** False policy rejects/accepts and invalid depth metrics.
- **Mitigation:** Standardize `root=0`; assert in delegation path and tests.

### RISK-D03: Cascade Completeness False Positive
- **Context:** ACK received does not always imply stable `Invalid`.
- **Risk:** Event marked complete while descendants remain valid/transient.
- **Mitigation:** Completion condition requires stable invalidated state for all expected capabilities.

### RISK-D04: TLA+ State Explosion
- **Context:** Unbounded agent/capability domain.
- **Risk:** TLC too slow for hackathon workflow.
- **Mitigation:** Model bounds (`N<=5`, `depth<=3`, finite op budgets), minimal variables.

---

## Phase 1 · Problem Framing and Scope Lock

**Goal:** Зафіксувати точні semantics для delegation depth policy та chain revocation guarantees.

### 1.1 Questions to Lock
1. What is authoritative depth definition? (`root=0`)
2. Which transitions are policy-gated during delegation?
3. What exactly counts as "cascade complete"?
4. How is per-depth unauthorized bound computed per strategy?

### 1.2 Deliverables
- [ ] Policy semantics doc (`depth`, `scope`, `remaining_ops`)
- [ ] Formal definition of cascade completion condition
- [ ] Bound function table `f(strategy, depth)`

---

## Phase 2 · Data Model and API Updates

**Goal:** Додати policy and verification primitives без зламу існуючого core demo.

### 2.1 Data Model Changes

```python
@dataclass(frozen=True)
class DelegationPolicy:
    max_depth: int
    require_scope_subset: bool = True
    propagate_remaining_ops: bool = True

@dataclass(frozen=True)
class RevocationEvent:
    id: UUID
    root_capability_id: UUID
    capability_id: UUID
    reason: RevocationReason
    issued_tick: int
    cascade: bool = False
    propagated: dict[UUID, Optional[int]] = field(default_factory=dict)
    expected_capabilities: set[UUID] = field(default_factory=set)
    invalidated_capabilities: set[UUID] = field(default_factory=set)
```

### 2.2 API Contracts

```python
class AuthorityService:
    def set_delegation_policy(self, policy: DelegationPolicy) -> None: ...
    def validate_delegation_depth(self, parent: Capability) -> bool: ...
    def get_cascade_status(self, event_id: UUID) -> dict:
        # expected, invalidated, completeness_ratio, pending
        ...

class ConsistencyMonitor:
    def register_expected_cascade(self, event_id: UUID, capability_ids: set[UUID]) -> None: ...
    def mark_capability_invalidated(self, event_id: UUID, capability_id: UUID, tick: int) -> None: ...
    def get_cascade_completeness_ratio(self, event_id: UUID) -> float: ...
```

### 2.3 Deliverables
- [ ] `DelegationPolicy` support in config + authority
- [ ] Revocation event fields for certificate tracking
- [ ] Cascade status API for report layer

---

## Phase 3 · Delegation Depth Policy Implementation

**Goal:** Guarantee bounded delegation before revocation even starts.

### 3.1 Rules
1. `child.depth = parent.depth + 1`
2. `child.depth <= max_depth`
3. `child.scope ⊆ parent.scope`
4. `child.max_operations <= parent.max_operations - parent.operations_used` (if bounded)

### 3.2 Error Semantics
- `DelegationDepthExceededError`
- `ScopeAttenuationError` (existing)
- `RemainingOpsPropagationError`

### 3.3 Tests
- [ ] allow at exact max depth
- [ ] deny above max depth
- [ ] deny child ops greater than remaining
- [ ] monotonicity on delegated ops budgets

---

## Phase 4 · Cascade Correctness Guarantees

**Goal:** Make cascade correctness measurable and auditable, not inferred.

### 4.1 BFS Completeness Certificate
1. On `revoke(root, cascade=True)`:
   - BFS descendants from `root_capability_id`
   - freeze `expected_capabilities`
2. During propagation:
   - each capability transition to stable `Invalid` marks `invalidated_capabilities`
3. Completion:
   - `invalidated_capabilities == expected_capabilities`

### 4.2 Per-Depth Unauthorized Bound
- Track unauthorized actions by `delegation_depth`.
- Evaluate bound function:

```text
unauthorized_ops(depth=d) <= f(strategy, d)
```

Where:
- `eager`: approx `v(d) * network_latency * (d+1)`
- `lazy`: `v(d) * (network_latency*(d+1) + check_interval)`
- `lease`: `v(d) * ttl`
- `exec_count`: `remaining_ops_at_revoke(d)` (deterministic cap)

### 4.3 Metrics
- `cascade_completeness_ratio`
- `cascade_completion_tick`
- `pending_capabilities_count`
- `bound_violations_by_depth`

### 4.4 Tests
- [ ] BFS expected set matches delegation graph descendants
- [ ] completeness reaches 100%
- [ ] no false completion while transient remains
- [ ] bound violation detector flags synthetic bad scenario

---

## Phase 5 · Minimal TLA+ Spec (Chain Revocation Invariants)

**Goal:** Formal confidence on invariants that matter for demo narrative.

### 5.1 Spec Scope
- **System model:** one root capability + bounded chain descendants.
- **Actions:** `Delegate`, `RevokeRoot`, `Propagate`, `TimeoutFailSafe`, `AttemptAction`.
- **State vars:** `capState`, `parent`, `depth`, `opsRemaining`, `expected`, `invalidated`, `unauthByDepth`.

### 5.2 Invariants

1. **Safety**
```text
RevokedParentImpliesEventuallyInvalidDescendants
```
`root revoked => descendants not permanently valid`

2. **Liveness**
```text
NoStuckTransient
```
`transient age > timeout => Invalid`

3. **Bound**
```text
DepthBoundHolds
```
`unauthByDepth[d] <= F(strategy, d)`

### 5.3 Files
- `formal/ChainRevocation.tla`
- `formal/ChainRevocation.cfg`
- `formal/README.md` (how to run TLC)

### 5.4 TLC Run Envelope
- Agents/caps: small bounded model
- Depth: `0..3`
- Strategies: encoded as finite constant

---

## Phase 6 · Demo and Reporting

**Goal:** Convert correctness into judge-visible story.

### 6.1 Scenario
- `scenarios/banking-depth-guarantee.yaml`
  - chain depth 3-4
  - root revoke at deterministic tick
  - strategy sweep (`eager`, `lazy`, `lease`, `exec_count`)

### 6.2 Terminal Narrative
1. Show depth policy deny on overflow.
2. Trigger root revoke.
3. Live print:
   - expected descendants
   - invalidated so far
   - completeness ratio
4. Show bound status by depth.

### 6.3 HTML Additions
- "Cascade Guarantee" section:
  - expected vs invalidated table
  - completion timeline
  - bound violations by strategy/depth

---

## Implementation Order (~10h)

```text
Step 1 (1.5h): DelegationPolicy + authority checks + depth/ops exceptions
Step 2 (2.0h): RevocationEvent certificate fields + monitor tracking
Step 3 (2.0h): Per-depth bound checker + metrics + report section
Step 4 (2.0h): TLA+ minimal spec + cfg + quick TLC runs
Step 5 (1.5h): Scenario/demo wiring + terminal output polish
Step 6 (1.0h): Tests, regression, README/formal notes
```

---

## Key Invariants to Verify in Code

1. `child.depth == parent.depth + 1`
2. `child.depth <= policy.max_depth`
3. `child.scope ⊆ parent.scope`
4. `child.max_ops <= parent.remaining_ops`
5. `cascade_complete => all expected are stable Invalid`
6. `bound_violations_by_depth` empty for valid reference runs

---

## Deliverables

- [ ] Policy-enforced delegation chain implementation
- [ ] Cascade completeness certificate and status API
- [ ] Per-depth bound evaluator and violation metrics
- [ ] Minimal TLA+ model with Safety/Liveness/Bound checks
- [ ] Banking depth guarantee scenario
- [ ] Updated report sections + demo script notes

---

## Non-Goals (Hackathon)

1. Full compositionality/interference proof for arbitrary N-agent systems.
2. Byzantine adversary model for propagation.
3. Full production OIDC/SCIM protocol integration.

---

## Demo Script (5 minutes)

1. **Policy gate (45s):** show delegation reject beyond `max_depth`.
2. **Root revoke (60s):** show BFS expected set and live convergence.
3. **Bound story (90s):** compare `unauthorized_by_depth` across strategies.
4. **Formal confidence (45s):** show TLC run: safety/liveness/bound pass.
5. **Takeaway (30s):** chain-safe revocation with measurable guarantees.

---

## Success Criteria

**Must-have**
- tests green
- no cascade completeness false positives
- depth policy enforced
- TLA+ invariants pass on bounded model

**Should-have**
- clean HTML "Cascade Guarantee" table
- deterministic scenario replay with stable metrics

**Nice-to-have**
- one-command runner combining simulation + report + formal check summary

