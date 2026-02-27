# TODO - Spec Alignment Tracker

Last updated: February 26, 2026  
Reference sources reviewed:

- `agent_revoke_consolidated_spec (1).md`
- `agent-revoke-plan-v2 (1).md`
- `agent_revoke_backlog.md`
- `open_questions.md`
- `CHANGELOG_V5 (1).md`

## Tier 0 / Tier 1 Alignment Status

- [x] B-001 Implementation spec (practical contract docs now in repo)
  - Added `docs/implementation-contract.md`
  - Added explicit terminal/report contracts and temporal invariant docs
- [x] B-002 Scenario schema and canonical files
  - `docs/scenario-schema.md`
  - `src/simulation/scenarios.py` validation and normalization
  - canonical scenario YAML files use authoritative exec-count values (10/500/1000)
- [x] B-003 Agentic IAM narrative to code paths
  - Added `docs/agentic-iam-code-mapping.md`
- [x] B-010 Terminal visualization contract
  - Added `docs/terminal-visualization-contract.md`
  - `src/output/terminal.py` updated to include optional tick-aware event formatting
- [x] B-011 HTML report contract
  - Added `docs/html-report-contract.md`
  - report APIs and template variables documented
- [x] B-013a Temporal logic formulations
  - Added `docs/temporal-logic-invariants.md`
- [~] B-013b Invariant proof (pen-and-paper/mechanized proof appendix)
  - Minimal formal model exists; full proof artifact still outstanding
- [~] B-013c TLA+ model and TLC checks
  - Minimal chain model implemented in `formal/tla/`; broader compositional coverage outstanding
- [x] B-014 Heterogeneous strategy
  - Implemented selector, schema support, engine integration, and tests
- [x] Align exception class names with consolidated spec contract
  - Added spec-aligned names in `src/core/exceptions.py` and maintained backward aliases
- [x] Add `DelegationEdge` dataclass
  - Added explicit edge type in `src/core/types.py`
  - Added `CapabilityRegistry.get_delegation_edges()`
- [x] Complete `ConsistencyMonitor` public API surface
  - Added/expanded `get_global_state`, `get_metrics`, `get_revocation_trace`,
    `get_delegation_tree`, `get_delegation_edges`, `get_delegation_graph`
- [x] Reconcile scenario YAML defaults to consolidated specification values
  - Updated banking, CRM, anomaly scenario parameters to spec-authoritative values

## Outstanding Work (ordered)

1. Produce full invariant proof artifact for Theorem 1 extensions (cascade completeness + transient liveness).
2. Expand TLA+ model beyond minimal chain to wider topologies and additional invariants.
3. Resolve strict `mypy` backlog while keeping existing strict settings intact.

## Recently Completed in This Pass

- Added missing specification-facing docs for implementation contracts and mappings.
- Added TODO tracker that mirrors backlog IDs and current state.
- Updated terminal output helpers to support spec-style tick-prefixed event rendering.
