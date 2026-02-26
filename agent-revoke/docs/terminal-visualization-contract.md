# Terminal Visualization Contract

Implementation file: `src/output/terminal.py`

## Event Renderers

- `print_grant(agent_id, resource, obo, tick=None)`
- `print_revoke(capability_id, reason, cascade, tick=None)`
- `print_ack(agent_id, mesi_transition, latency, tick=None)`
- `print_deny(agent_id, resource, reason, tick=None)`
- `print_action(agent_id, resource, tick=None)`
- `print_exhausted(agent_id, ops_used, max_ops, tick=None)`
- `print_deleg(from_agent, to_agent, scope, tick=None)`

All renderers support optional tick-prefix formatting while remaining backward-compatible with existing calls.

## State and Summary Views

- `build_state_table(agents)`:
  - per-agent MESI states
  - trust score column
- `build_summary_panel(metrics)`:
  - unauthorized count
  - staleness max
  - cascade completeness ratio
  - transient timeout count

## Live Update Surface

- `SimulationLiveView(enabled=False)`:
  - `start()`, `update(...)`, `stop()`
- `LiveDashboard` context manager:
  - wraps live rendering for demo mode
  - `update(tick, agents, scenario_name, strategy_name)`
