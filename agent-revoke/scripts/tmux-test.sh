#!/bin/bash
# agent-revoke: Test session
# Layout: unit | coverage | strategies | integration

SESSION="ar-test"
DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

tmux kill-session -t $SESSION 2>/dev/null
tmux new-session -d -s $SESSION -c "$DIR"

tmux rename-window -t $SESSION:1 "unit"
tmux send-keys -t $SESSION:1 "echo 'pytest tests/ -k \"not integration\" -v'" Enter

tmux new-window -t $SESSION -n "coverage" -c "$DIR"
tmux send-keys -t $SESSION:coverage "echo 'pytest --cov=src --cov-report=term-missing tests/'" Enter

tmux new-window -t $SESSION -n "strategies" -c "$DIR"
tmux send-keys -t $SESSION:strategies "echo 'pytest tests/ -k strategy -v'" Enter

tmux new-window -t $SESSION -n "integration" -c "$DIR"
tmux send-keys -t $SESSION:integration "echo 'pytest tests/ -k simulation -v'" Enter

tmux select-window -t $SESSION:1
tmux attach-session -t $SESSION
