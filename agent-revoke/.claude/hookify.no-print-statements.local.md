---
name: no-print-statements
enabled: true
event: stop
pattern: .*
action: warn
---

**Before stopping, check for stray print() statements in modified files.**

Run: `git diff --name-only | xargs grep -n 'print(' 2>/dev/null`

This project uses `logging` — print() calls should not be committed. Replace with `logger.debug()`, `logger.info()`, or `logger.error()`.
