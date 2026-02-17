# Enforce Standards

Run the code-standards-enforcer agent to audit and fix standards compliance. Usage: `/enforce [action]`

## Actions

### No argument or `audit` — Full compliance audit
Run all quality gates and report status:
1. `ruff check src/ tests/` — lint violations
2. `ruff format --check src/ tests/` — formatting issues
3. `python -m mypy src/ --strict` — type errors
4. `pytest --cov=src --cov-report=term-missing --cov-fail-under=80 tests/` — coverage
5. Check for print statements: `ruff check src/ --select T201`
6. Present compliance report table

### `fix` — Auto-fix what's possible
1. `ruff check --fix src/ tests/` — auto-fix lint issues
2. `ruff format src/ tests/` — auto-format
3. Re-run audit to show remaining manual fixes

### `setup` — Initialize or update tool config
Ensure pyproject.toml has correct ruff, mypy, and pytest sections.
Set up .pre-commit-config.yaml if missing.

### `gate` — Run checkpoint gate checks
Same as the checkpoint gate from project-execution.md:
1. pytest full suite
2. mypy strict
3. ruff check + format check
4. Report pass/fail for phase advancement decision

## Integration

- `/enforce audit` before `/review` catches mechanical issues first
- `/enforce fix` auto-resolves formatting before human review
- `/enforce gate` runs at every phase transition
- Chains: `/enforce fix` → `/review` → `/pr-checklist`
