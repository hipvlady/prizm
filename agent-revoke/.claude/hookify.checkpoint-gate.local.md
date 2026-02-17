---
name: checkpoint-gate
enabled: true
event: stop
pattern: .*
action: warn
---

**Checkpoint gate — verify before stopping.**

1. Run `python -m pytest tests/ -v` (full suite must pass)
2. Run `python -m mypy src/ --strict` (no type errors)
3. Check for stray `print()`: `git diff --name-only | xargs grep -n 'print(' 2>/dev/null`
4. Update memory/decisions.md if any architectural choices were made
5. Update memory/bugs.md if any edge cases were discovered

Do NOT stop if tests or mypy are failing.
