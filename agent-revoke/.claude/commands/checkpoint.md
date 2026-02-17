Verify demo checkpoint for Step $ARGUMENTS is met.

Run review-invariants for all files modified in Step $ARGUMENTS.
Run the associated test suite: python -m pytest tests/ -k step$ARGUMENTS -v
If Step 4+: run scenario-run for the relevant scenario.

Report: PASS or FAIL with specific blockers listed.
Only proceed to next step on PASS.
