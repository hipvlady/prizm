---
name: guard-invariants
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: operations_used\s*[-=]|operations_used\s*-=|\.operations_used\s*=\s*0|DFS|recursive.*revok|revok.*recursive
action: block
---

**INVARIANT VIOLATION DETECTED — edit blocked.**

Critical invariants that must never be violated:
1. operations_used is monotonic — NEVER decrement it
2. Cascade revocation uses BFS, not recursive DFS
3. child.scope must be a subset of parent.scope

If you need to reset operations_used for testing, use a new Capability instance instead.
