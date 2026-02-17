---
name: enforce-agent-ownership
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/(authority|agent|core|strategies|simulation|output)/
action: warn
---

**Check agent file ownership before editing.**

| Path | Owner |
|------|-------|
| src/core/*, src/strategies/* | mesi-domain-engineer |
| src/authority/*, src/agent/* | authority-runtime-engineer |
| src/simulation/*, src/output/* | simulation-scenario-engineer |

Verify you are the correct agent for this file. Cross-ownership edits violate orchestration rules.
