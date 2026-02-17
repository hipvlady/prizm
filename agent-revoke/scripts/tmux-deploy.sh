#!/bin/bash
# agent-revoke: Deploy/demo session
# Layout: demo | scenarios | report | rollback

SESSION="ar-deploy"
DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

tmux kill-session -t $SESSION 2>/dev/null
tmux new-session -d -s $SESSION -c "$DIR"

tmux rename-window -t $SESSION:1 "demo"
tmux send-keys -t $SESSION:1 "echo 'python -m src.simulation.engine --scenario scenarios/banking.yaml'" Enter

tmux new-window -t $SESSION -n "scenarios" -c "$DIR"
tmux send-keys -t $SESSION:scenarios "echo 'ls scenarios/*.yaml'" Enter

tmux new-window -t $SESSION -n "report" -c "$DIR"
tmux send-keys -t $SESSION:report "echo 'python -m src.output.report'" Enter

tmux new-window -t $SESSION -n "rollback" -c "$DIR"
tmux send-keys -t $SESSION:rollback "echo '=== Rollback ==='" Enter
tmux send-keys -t $SESSION:rollback "echo 'git log --oneline -5'" Enter
tmux send-keys -t $SESSION:rollback "echo 'git revert HEAD'" Enter

tmux select-window -t $SESSION:1
tmux attach-session -t $SESSION
