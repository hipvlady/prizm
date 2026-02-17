# Architecture Decision Records

## ADR-001: PDP/PEP Separation via Message Passing

AuthorityService (PDP) never directly mutates AgentState.
Communication only via RevocationEvent messages.

**Rationale:** Mirrors real-world OAuth/RBAC separation; makes strategies pluggable.

## ADR-002: Tick-Based Logical Clock

Use integer tick counter, not wall clock. Deterministic replays, controllable latency injection.

## ADR-003: Consistency-Agnostic vs Consistency-Directed Classification

- **Eager** = Consistency-Agnostic (SWMR, blocks until all ACK).
- **Lazy/Lease/Exec-Count** = Consistency-Directed (relaxed, bounded staleness).

**Source:** Sorin/Hill/Wood Ch.2 §2.3.

## ADR-004: BFS for Cascade Revocation

Cascade traversal uses BFS on delegation tree, not recursive DFS.

**Rationale:** Prevents stack overflow on deep delegation chains.
