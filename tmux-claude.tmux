#!/usr/bin/env bash

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create scripts directory if it doesn't exist
mkdir -p "$CURRENT_DIR/scripts"

# Make Python scripts executable
chmod +x "$CURRENT_DIR/scripts/claude_tmux_hooks.py"
chmod +x "$CURRENT_DIR/scripts/tmux_integration.py"
chmod +x "$CURRENT_DIR/scripts/pane_tracker.py"
chmod +x "$CURRENT_DIR/scripts/notification_handler.py"

# Set up tmux hooks for monitoring pane activity
tmux set-hook -g after-select-pane "run-shell '$CURRENT_DIR/scripts/pane_tracker.py monitor'"
tmux set-hook -g pane-exited "run-shell '$CURRENT_DIR/scripts/pane_tracker.py cleanup %1'"

# Display installation message
tmux display-message "Claude Tmux Plugin loaded. Configure hooks in ~/.claude/settings.json"