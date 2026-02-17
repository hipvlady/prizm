---
name: tmux-reminder
enabled: true
event: bash
pattern: pytest\s|mypy\s|pip\s+install|python\s+-m\s+(pytest|mypy|pip|src\.simulation)|ruff\s+(check|format)\s+\S+.*\S|python\s+-m\s+src\.(simulation|output)
action: warn
---

**Long-running command detected.**

Consider running in tmux if not already in a session:
- `/tmux create dev` — spin up dev session
- `/tmux send ar-dev:tests <command>` — run in background window

Commands like pytest, mypy, ruff, pip install, and simulation runs can take >30 seconds.
