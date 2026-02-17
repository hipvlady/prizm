---
name: protect-memory-files
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: memory/(decisions|bugs|key_facts)\.md$
action: warn
---

**Editing a shared memory file.**

Memory files are read by all subagents at task start. Ensure:
- Entries are append-only (don't delete previous decisions)
- ADRs in decisions.md follow the existing format
- bugs.md includes reproduction steps
- key_facts.md stays concise — it's loaded into every agent's context
