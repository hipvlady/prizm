Run scenario $ARGUMENTS and validate outputs.

1. python -m src.simulation.engine --scenario=$ARGUMENTS
2. Verify terminal output has correct format (timestamps, MESI labels, symbols)
3. For crm-bulk-ops: confirm exec-count shows exactly N unauthorized ops
   (this is the killer demo differentiator — must be numerically verifiable)
4. Save metrics snapshot: python -m src.simulation.engine --scenario=$ARGUMENTS --export-metrics=memory/metrics-$ARGUMENTS.json
5. Report: what worked, deviations from expected behavior, any MESI violations
