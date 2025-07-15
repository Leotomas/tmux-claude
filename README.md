# Claude Tmux Plugin

A tmux plugin that displays emoji status indicators in pane names when Claude Code finishes responding or sends notifications. The plugin tracks multiple Claude instances across different tmux panes and shows the appropriate emoji for each pane.

## Features

- **✅ Stop Status**: Shows checkmark emoji when Claude finishes responding
- **📢 Notification Status**: Shows notification emoji when Claude sends notifications
- **Multi-pane Support**: Tracks multiple Claude instances across different tmux panes
- **Smart Restoration**: Automatically restores original pane names when user switches panes or presses Enter
- **System Notifications**: Sends notifications using `notify_windows` command
- **Pure Python**: No external dependencies, uses only Python 3 standard library

## Installation

### Using TPM (Tmux Plugin Manager)

1. Add the plugin to your `~/.tmux.conf`:
   ```bash
   set -g @plugin 'your-username/tmux-claude'
   ```

2. Press `prefix + I` to install the plugin.

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/tmux-claude.git ~/.tmux/plugins/tmux-claude
   ```

2. Add to your `~/.tmux.conf`:
   ```bash
   run-shell ~/.tmux/plugins/tmux-claude/tmux-claude.tmux
   ```

3. Reload tmux configuration:
   ```bash
   tmux source-file ~/.tmux.conf
   ```

## Configuration

### Recommended: Disable Automatic Renaming

For optimal plugin functionality, it's recommended to disable tmux's automatic window renaming. Add this to your `~/.tmux.conf`:

```bash
# Disable automatic window renaming to preserve custom names with emoji status
set-option -g automatic-rename off
set-option -g automatic-rename-format ''
```

This ensures that:
- Your custom window names are preserved when emoji prefixes are added
- The plugin doesn't conflict with tmux's automatic renaming
- Window names remain stable across different commands and processes

**Note**: The plugin will work with automatic renaming enabled, but your custom window names may be overridden by tmux's auto-generated names.

### Claude Code Hooks Setup

Add the following configuration to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/tmux-claude/scripts/claude_tmux_hooks.py stop"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/tmux-claude/scripts/claude_tmux_hooks.py notification"
          }
        ]
      }
    ]
  }
}
```

**Important**: Replace `/path/to/tmux-claude/` with the actual path to your plugin installation.

### Example Configuration

Use the provided `example-claude-settings.json` as a template and adjust the paths according to your installation.

## Usage

1. **Start Claude in tmux panes**: Run Claude Code in different tmux panes as usual.

2. **Automatic status updates**: The plugin automatically detects when Claude finishes or sends notifications and updates the pane names with appropriate emojis.

3. **Restore original names**: When you switch to a pane or press Enter, the original pane name is automatically restored.

4. **View status**: Check the status of all tracked panes:
   ```bash
   ~/.tmux/plugins/tmux-claude/scripts/pane_tracker.py status
   ```

## Commands

### Manual Testing

Test the notification system:
```bash
./scripts/notification_handler.py test
```

Test emoji status in current pane:
```bash
./scripts/claude_tmux_hooks.py stop
./scripts/claude_tmux_hooks.py notification
```

Restore original pane name:
```bash
./scripts/claude_tmux_hooks.py restore
```

### Debugging

List all tmux panes:
```bash
./scripts/tmux_integration.py list-panes
```

Find panes running Claude:
```bash
./scripts/tmux_integration.py find-claude
```

View tracked panes status:
```bash
./scripts/pane_tracker.py status
```

## How It Works

1. **Hook Integration**: Claude Code hooks trigger the plugin when Claude stops or sends notifications.

2. **Pane Detection**: The plugin identifies which tmux pane the Claude instance is running in using the `$TMUX_PANE` environment variable, ensuring the emoji appears on the correct pane even when you're working in a different pane.

3. **Emoji Prefixes**: The plugin adds emoji prefixes to window names:
   - ✅ when Claude finishes (`Stop` hook)
   - 📢 when Claude sends notifications (`Notification` hook)

4. **Activity Monitoring**: The plugin monitors pane activity and restores original names when users switch panes or press Enter.

5. **State Management**: Pane states are stored in temporary JSON files and cleaned up automatically.

6. **Multi-Pane Support**: Works correctly across multiple tmux panes running different Claude instances simultaneously.

## File Structure

```
tmux-claude/
├── tmux-claude.tmux              # Main plugin file
├── scripts/
│   ├── claude_tmux_hooks.py      # Hook handler (Stop/Notification)
│   ├── tmux_integration.py       # Tmux pane management
│   ├── pane_tracker.py           # Pane activity monitoring
│   └── notification_handler.py   # System notifications
├── example-claude-settings.json  # Example Claude configuration
└── README.md                     # This file
```

## Requirements

- **Python 3.6+** (required)
- tmux
- Claude Code with hooks support
- `notify_windows` command (optional, for notifications)

## Debug Logging

The plugin includes comprehensive debug logging to help troubleshoot issues.

### Enable Debug Logging

```bash
# Enable debug logging
./scripts/debug_logger.py enable

# Or set environment variable
export TMUX_CLAUDE_DEBUG=1
```

### View Debug Logs

```bash
# View all recent logs
./scripts/debug_logger.py view

# View logs for specific script
./scripts/debug_logger.py view claude_tmux_hooks

# View logs for specific script (other examples)
./scripts/debug_logger.py view tmux_integration
./scripts/debug_logger.py view pane_tracker
./scripts/debug_logger.py view notification_handler
```

### Clear Debug Logs

```bash
# Clear all log files
./scripts/debug_logger.py clear
```

### Disable Debug Logging

```bash
# Disable debug logging
./scripts/debug_logger.py disable
```

### Log File Locations

Debug logs are stored in `scripts/.logs/`:
- `claude_tmux_hooks.log` - Hook execution logs
- `tmux_integration.log` - Tmux command logs
- `pane_tracker.log` - Pane tracking and monitoring logs
- `notification_handler.log` - Notification system logs
- `tmux_claude.log` - Combined main log

## Troubleshooting

### Plugin not loading
- Ensure the plugin files are executable
- Check tmux configuration syntax
- Verify Python 3 is available
- **Debug**: Enable logging and check `tmux_claude.log`

### Window names not preserved
- Disable automatic renaming in `~/.tmux.conf` (see Configuration section)
- Check if you have custom window names set with `tmux rename-window`
- **Debug**: Check logs for "auto_rename_was_on" entries

### Hooks not working
- Verify the paths in `~/.claude/settings.json` are correct
- Check that Claude Code supports hooks
- Test the hook scripts manually
- **Debug**: Enable logging and run `./scripts/claude_tmux_hooks.py stop` manually

### Notifications not working
- Test notification system: `./scripts/notification_handler.py test`
- Ensure `notify_windows` command is available
- Check system notification settings
- **Debug**: Check `notification_handler.log` for error messages

### Emoji not showing
- Verify terminal supports Unicode
- Check tmux pane name display settings
- Test manually: `./scripts/claude_tmux_hooks.py stop`
- **Debug**: Check `claude_tmux_hooks.log` for pane name setting errors

### Emoji appears on wrong pane
- The plugin uses `$TMUX_PANE` environment variable to detect the correct pane
- If testing manually, ensure you're in the correct pane context
- **Debug**: Check logs for "Got pane ID from TMUX_PANE" entries
- **Fix**: Use `TMUX_PANE=%X ./scripts/claude_tmux_hooks.py stop` to specify pane

### Common Debug Commands

```bash
# Enable debug and test stop hook
./scripts/debug_logger.py enable
./scripts/claude_tmux_hooks.py stop
./scripts/debug_logger.py view claude_tmux_hooks

# Test notification system
./scripts/notification_handler.py test
./scripts/debug_logger.py view notification_handler

# Check pane tracking
./scripts/pane_tracker.py status
./scripts/debug_logger.py view pane_tracker

# Test pane detection
echo "Current pane: $(tmux display-message -p '#{pane_id}'), TMUX_PANE: $TMUX_PANE"
./scripts/claude_tmux_hooks.py stop
./scripts/debug_logger.py view claude_tmux_hooks | grep TMUX_PANE
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]