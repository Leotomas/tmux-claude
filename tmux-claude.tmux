#!/usr/bin/env bash

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create scripts directory if it doesn't exist
mkdir -p "$CURRENT_DIR/scripts"

# Make Python scripts executable
chmod +x "$CURRENT_DIR/scripts/claude_tmux_hooks.py"
chmod +x "$CURRENT_DIR/scripts/tmux_integration.py"
chmod +x "$CURRENT_DIR/scripts/pane_tracker.py"
chmod +x "$CURRENT_DIR/scripts/notification_handler.py"
chmod +x "$CURRENT_DIR/scripts/debug_logger.py"

# Set up tmux hooks for monitoring pane activity and input
tmux set-hook -g after-select-pane "run-shell '$CURRENT_DIR/scripts/pane_tracker.py monitor #{pane_id}'"
tmux set-hook -g pane-exited "run-shell '$CURRENT_DIR/scripts/pane_tracker.py cleanup #{pane_id}'"


# Also try to hook into window selection
tmux set-hook -g after-select-window "run-shell '$CURRENT_DIR/scripts/claude_tmux_hooks.py restore #{pane_id}'"

# Bind Enter key to clear emoji prefix when pressed
tmux bind-key -n Enter run-shell "tmux send-keys Enter; '$CURRENT_DIR/scripts/claude_tmux_hooks.py' clear_emoji_on_enter"

# Display installation message
tmux display-message "Claude Tmux Plugin loaded. Configure hooks in ~/.claude/settings.json"