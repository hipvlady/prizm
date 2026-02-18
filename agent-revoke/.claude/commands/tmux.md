# Tmux Session Manager

Manage tmux sessions for agent-revoke. Usage: `/tmux <action> [args]`

## Actions

Parse the argument to determine the action:

### `create <template>` — Create session from template
Templates: `dev`, `test`, `deploy`

Run: `bash scripts/tmux-<template>.sh`

| Template | Session | Windows |
|----------|---------|---------|
| dev | ar-dev | editor, tests, mypy, git |
| test | ar-test | unit, coverage, strategies, integration |
| deploy | ar-deploy | demo, scenarios, report, rollback |

### `list` — List active sessions
Run: `tmux list-sessions 2>/dev/null || echo "No active sessions"`

### `attach <session>` — Reattach to session
Run: `tmux attach-session -t <session>`

### `detach` — Detach current session
Run: `tmux detach-client`

### `kill <session>` — Kill a session
Run: `tmux kill-session -t <session>`

Confirm with user before killing.

### `windows <session>` — List windows in session
Run: `tmux list-windows -t <session>`

### `send <session>:<window> <command>` — Send command to window
Run: `tmux send-keys -t <session>:<window> "<command>" Enter`

Useful for running long commands in background tmux windows without blocking Claude.

### No argument — Show status
Run `tmux list-sessions` and show a summary table of active sessions with window counts.

## Examples

```
/tmux create dev          → Creates ar-dev session
/tmux list                → Shows all active sessions
/tmux send ar-test:unit pytest tests/ -k mesi -v
/tmux kill ar-test        → Kills test session
```
