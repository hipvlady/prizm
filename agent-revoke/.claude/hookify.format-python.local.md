---
name: python-quality-check
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
action: warn
---

**Python file modified.** Before moving on:
1. Run `ruff format` and `ruff check --fix` on the changed file
2. Run `python -m mypy src/ --strict` to verify type safety

This project enforces strict type checking at every checkpoint gate.
