#!/bin/bash
# agent-revoke: Dev session
# Layout: editor | tests | mypy | git

SESSION="ar-dev"
DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

tmux kill-session -t $SESSION 2>/dev/null
tmux new-session -d -s $SESSION -c "$DIR"

tmux rename-window -t $SESSION:1 "editor"

tmux new-window -t $SESSION -n "tests" -c "$DIR"
tmux send-keys -t $SESSION:tests "echo 'pytest tests/ -v --tb=short'" Enter

tmux new-window -t $SESSION -n "mypy" -c "$DIR"
tmux send-keys -t $SESSION:mypy "echo 'python -m mypy src/ --strict'" Enter

tmux new-window -t $SESSION -n "git" -c "$DIR"
tmux send-keys -t $SESSION:git "git status" Enter

tmux select-window -t $SESSION:1
tmux attach-session -t $SESSION
