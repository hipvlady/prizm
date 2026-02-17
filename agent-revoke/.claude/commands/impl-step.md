Implement critical path Step $ARGUMENTS for agent-revoke.

Before writing code:
1. Read memory/decisions.md — relevant ADRs
2. Read memory/bugs.md — risks for this step
3. Read memory/key_facts.md — stack constraints
4. State the demo checkpoint for this step before writing any code

Implement:
- Python 3.11+, type hints on every function and method
- @dataclass(frozen=True) for immutable types
- Enum + match/case for state machines
- ABC for strategy interface
- No bare except, no type: ignore
- Tests cover: happy path, invalid transition, cascade, boundary at max_operations=0 and max_operations=None

Verify:
1. python -m pytest tests/ -k $ARGUMENTS -v
2. python -m mypy src/ --strict (or ruff check src/)
3. Confirm demo checkpoint is achievable in isolation

After:
- Update memory/decisions.md if architectural choice was made
- Update memory/bugs.md if coherence edge case discovered
- Log: "Step N complete. Xh elapsed, Yh remaining."
