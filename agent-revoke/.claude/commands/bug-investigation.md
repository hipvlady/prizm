# Bug Investigation Framework

Structured approach: Reproduce → Analyze → Fix → Prevent. Provide the bug description or error message as argument: `/bug-investigation <description>`

## Phase 1: Reproduce

1. **Identify symptoms**: What's the exact error message or unexpected behavior?
2. **Find minimal reproduction**: Create the smallest test case that triggers the bug
3. **Write failing test**: Add a test in `tests/` that demonstrates the bug
   ```
   def test_bug_<short_description>():
       # Minimal reproduction
       ...
       assert expected == actual  # This should FAIL
   ```
4. **Confirm reproduction**: Run `pytest tests/ -k "bug_<short_description>" -v` — must fail

## Phase 2: Analyze

5. **Trace execution**: Read the code path from entry point to failure
6. **Check invariants**: Does the bug violate any of these?
   - child.scope ⊆ parent.scope
   - operations_used monotonic
   - BFS cascade (not DFS)
   - max_operations=None = unbounded
7. **Root cause**: Identify the exact line(s) causing the issue
8. **Blast radius**: What else could be affected? Check callers and dependents

## Phase 3: Fix

9. **Implement fix**: Make the minimal change that addresses the root cause
10. **Verify fix**: Run the failing test — must now pass
11. **Regression check**: Run `python -m pytest tests/ -v` — no new failures
12. **Type check**: Run `python -m mypy src/ --strict` — no new errors

## Phase 4: Prevent

13. **Add guard**: If the bug was an invariant violation, add a runtime check:
    ```python
    if not condition:
        raise InvariantError("description of what went wrong")
    ```
14. **Document**: Add entry to `memory/bugs.md`:
    ```
    ## Bug: <title>
    - Symptom: <what happened>
    - Root cause: <why>
    - Fix: <what changed>
    - Prevention: <guard added>
    ```
15. **Review similar code**: Search for the same pattern elsewhere

## Report

| Phase | Status | Details |
|-------|--------|---------|
| Reproduction | CONFIRMED/UNABLE | test name |
| Root cause | IDENTIFIED/UNCLEAR | file:line |
| Fix | APPLIED/PENDING | description |
| Tests | PASS/FAIL | suite results |
| Prevention | GUARD ADDED/DOCUMENTED | what was added |

## Chain

After fix is verified, suggest: **Bug fixed. Run `/pr-checklist` before merging.**
