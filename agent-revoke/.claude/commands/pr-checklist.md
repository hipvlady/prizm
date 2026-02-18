# Pre-PR Checklist

Run this checklist before creating a pull request. Execute each step and report pass/fail.

## Automated Checks

1. **Tests**: Run `python -m pytest tests/ -v --tb=short` — all must pass
2. **Type check**: Run `python -m mypy src/ --strict` — no errors
3. **Lint**: Run `ruff check src/ tests/` — no violations
4. **Format**: Run `ruff format --check src/ tests/` — no changes needed
5. **Print statements**: Run `git diff main --name-only -- '*.py' | xargs grep -n 'print(' 2>/dev/null` — should be empty

## Manual Review

6. **Diff review**: Run `git diff main --stat` and review each changed file for:
   - No debug code left behind
   - No hardcoded secrets or credentials
   - No TODO/FIXME that should be resolved
   - Docstrings on public functions

7. **Invariant check** (if src/core/ or src/strategies/ changed):
   - child.scope ⊆ parent.scope
   - operations_used is monotonic
   - Cascade uses BFS not DFS
   - max_operations=None means unbounded

8. **Memory update**: Check if memory/decisions.md or memory/bugs.md needs updating

## Report

Present results as a table:

| Check | Status | Details |
|-------|--------|---------|
| Tests | PASS/FAIL | X passed, Y failed |
| Types | PASS/FAIL | error count |
| Lint | PASS/FAIL | violation count |
| Format | PASS/FAIL | files needing format |
| Print stmts | PASS/FAIL | locations found |
| Diff review | PASS/FAIL | issues found |
| Invariants | PASS/FAIL/N/A | violations |
| Memory | UPDATED/SKIPPED | what changed |

## Chain

If all checks pass, suggest: **Ready for PR. Run `/deployment-workflow` if deploying, or create PR now.**
