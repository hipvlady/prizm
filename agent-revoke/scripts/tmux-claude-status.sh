#!/bin/bash
# Outputs Claude project context for tmux status line
# Usage in tmux.conf: #(path/to/tmux-claude-status.sh)

STATE_FILE="${HOME}/.claude/claude-tmux-state"
PROJECT="agent-revoke"

# Check if claude is running in any pane
CLAUDE_PANES=$(tmux list-panes -a -F '#{pane_current_command}' 2>/dev/null | grep -c claude)

if [ "$CLAUDE_PANES" -gt 0 ]; then
    # Read phase from state file if it exists
    if [ -f "$STATE_FILE" ]; then
        PHASE=$(cat "$STATE_FILE")
        echo "$PROJECT [$PHASE] ${CLAUDE_PANES}p"
    else
        echo "$PROJECT ${CLAUDE_PANES}p"
    fi
else
    echo "$PROJECT idle"
fi
