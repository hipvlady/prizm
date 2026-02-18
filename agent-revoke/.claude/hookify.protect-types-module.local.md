---
name: protect-types-module
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/core/types\.py$
action: warn
---

**Editing the canonical types module (src/core/types.py).**

This is the single source of truth for all domain types. Before saving:
- All types MUST be exported from this file (invariant)
- Verify child.scope is a subset of parent.scope in any Capability changes
- Verify max_operations=None means unbounded, not zero
- Verify operations_used is never decremented (monotonic invariant)
- Only mesi-domain-engineer should edit this file
