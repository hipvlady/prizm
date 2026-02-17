# Refactor Guide

Structured refactoring: Assess → Plan → Execute → Verify. Provide the target as argument: `/refactor-guide <file or module>`

## Phase 1: Assess — Should We Refactor?

1. **Read the target code**: Understand current structure
2. **Smell check**: Does it have any of these?
   - Function > 30 lines
   - 4+ parameters
   - Duplicated logic (3+ occurrences)
   - Mixed abstraction levels
   - Mutable state where immutable would work
   - God class / do-everything module
3. **Cost-benefit**: Is the refactor worth it right now?
   - YES if: blocking current task, causing bugs, touched frequently
   - NO if: working fine, rarely changed, cosmetic only
   - DEFER if: valid but not on critical path (add to memory/decisions.md)

## Phase 2: Plan — How to Refactor

4. **Identify pattern**: Which refactoring applies?

   | Smell | Refactoring | Example |
   |-------|-------------|---------|
   | Long function | Extract function | Split into composable parts |
   | Mutable state | Immutable data | Return new objects, don't mutate |
   | Duplicated logic | Extract + parameterize | Shared utility with arguments |
   | Deep nesting | Early return / guard clause | Flatten conditionals |
   | God class | Split by responsibility | One class = one job |
   | Stringly typed | Enum / dataclass | Replace magic strings |

5. **Scope boundary**: Define what changes and what doesn't
6. **Ensure test coverage**: Run `pytest --cov=<module> tests/` — if < 80%, write tests first

## Phase 3: Execute — Make the Change

7. **Tests green first**: `pytest tests/ -v` must pass before any changes
8. **Small steps**: One refactoring at a time, test between each
9. **Preserve behavior**: No feature changes mixed with refactoring
10. **Respect ownership**: Check agent ↔ file mapping before editing:
    - src/core/*, src/strategies/* → mesi-domain-engineer
    - src/authority/*, src/agent/* → authority-runtime-engineer
    - src/simulation/*, src/output/* → simulation-scenario-engineer

## Phase 4: Verify — Confirm No Regression

11. **Full test suite**: `python -m pytest tests/ -v`
12. **Type check**: `python -m mypy src/ --strict`
13. **Diff review**: `git diff --stat` — only expected files changed?
14. **Invariant check**: No violations of the 6 critical invariants

## Report

| Phase | Status | Details |
|-------|--------|---------|
| Assessment | REFACTOR/DEFER/SKIP | reason |
| Pattern | <which refactoring> | |
| Pre-coverage | X% | target module |
| Execution | COMPLETE/PARTIAL | files changed |
| Tests | PASS/FAIL | |
| Types | PASS/FAIL | |
| Post-coverage | X% | improvement |

## Chain

After refactor is verified, suggest: **Refactor complete. Run `/pr-checklist` before merging.**
