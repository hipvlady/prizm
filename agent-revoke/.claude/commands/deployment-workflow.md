# Deployment Workflow

Pre-deploy verification, deployment steps, and rollback plan. Run `/pr-checklist` first if not already done.

## Pre-Deploy Verification

1. **PR status**: Confirm PR is merged to main
2. **Full test suite**: Run `python -m pytest tests/ -v` on main branch
3. **Type safety**: Run `python -m mypy src/ --strict` on main branch
4. **Dependencies**: Check `requirements.txt` is up to date — run `pip freeze | diff - requirements.txt`
5. **Breaking changes**: Review commits since last deploy for API/schema changes

## Deploy Steps

6. **Tag release**: `git tag -a v<version> -m "Release v<version>"`
7. **Build**: Verify `python -m py_compile src/**/*.py` succeeds (no syntax errors)
8. **Smoke test**: Run the primary scenario to verify end-to-end:
   ```
   python -m src.simulation.engine --scenario scenarios/banking.yaml --strategy eager
   ```

## Post-Deploy Verification

9. **Health check**: Verify all 4 strategies produce expected output
10. **Report generation**: Verify HTML report generates correctly
11. **Terminal viz**: Verify rich terminal output renders

## Rollback Plan

If any post-deploy check fails:
1. `git revert HEAD` (if single commit) or `git revert <merge-commit> -m 1`
2. Re-run smoke test on reverted code
3. Document failure in memory/bugs.md

## Report

| Phase | Status | Details |
|-------|--------|---------|
| Pre-deploy checks | PASS/FAIL | |
| Build | PASS/FAIL | |
| Smoke test | PASS/FAIL | |
| Post-deploy verify | PASS/FAIL | |
| Rollback needed | YES/NO | |

## Chain

If all checks pass, suggest: **Deploy complete. Run `/pr-checklist` on next feature branch when ready.**
