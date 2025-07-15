#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from debug_logger import DebugLogger

# Initialize debug logger
logger = DebugLogger('claude_tmux_hooks')

def get_script_dir():
    """Get the directory where this script is located"""
    return Path(__file__).parent

def get_current_tmux_pane():
    """Get the current tmux pane ID"""
    logger.log_function_call('get_current_tmux_pane')
    try:
        cmd = ['tmux', 'display-message', '-p', '#{pane_id}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pane_id = result.stdout.strip()
        logger.log_tmux_command(cmd, pane_id)
        logger.debug(f"Current pane ID: {pane_id}")
        return pane_id
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'display-message', '-p', '#{pane_id}'], error=str(e))
        logger.error(f"Failed to get current pane ID: {e}")
        return None

def get_current_tmux_session():
    """Get the current tmux session name"""
    logger.log_function_call('get_current_tmux_session')
    try:
        cmd = ['tmux', 'display-message', '-p', '#{session_name}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        session_name = result.stdout.strip()
        logger.log_tmux_command(cmd, session_name)
        logger.debug(f"Current session: {session_name}")
        return session_name
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'display-message', '-p', '#{session_name}'], error=str(e))
        logger.error(f"Failed to get current session: {e}")
        return None

def get_pane_name(pane_id):
    """Get the current window name of a tmux pane"""
    logger.log_function_call('get_pane_name', args=[pane_id])
    try:
        cmd = ['tmux', 'display-message', '-p', '-t', pane_id, '#{window_name}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pane_name = result.stdout.strip()
        logger.log_tmux_command(cmd, pane_name)
        logger.debug(f"Pane {pane_id} window name: {pane_name}")
        return pane_name
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'display-message', '-p', '-t', pane_id, '#{window_name}'], error=str(e))
        logger.error(f"Failed to get window name for {pane_id}: {e}")
        return None

def get_window_auto_rename_status(pane_id):
    """Check if automatic-rename is enabled for a specific window"""
    logger.log_function_call('get_window_auto_rename_status', args=[pane_id])
    try:
        cmd = ['tmux', 'show-options', '-t', pane_id, 'automatic-rename']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        logger.log_tmux_command(cmd, output)
        # Parse output like "automatic-rename on" or "automatic-rename off"
        is_on = 'on' in output
        logger.debug(f"Window {pane_id} automatic-rename: {is_on}")
        return is_on
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'show-options', '-t', pane_id, 'automatic-rename'], error=str(e))
        logger.debug(f"Could not get automatic-rename status for {pane_id}, assuming off")
        return False

def set_window_auto_rename(pane_id, enabled):
    """Enable or disable automatic-rename for a specific window"""
    logger.log_function_call('set_window_auto_rename', args=[pane_id, enabled])
    try:
        value = 'on' if enabled else 'off'
        cmd = ['tmux', 'set-option', '-t', pane_id, 'automatic-rename', value]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.log_tmux_command(cmd, "SUCCESS")
        logger.debug(f"Set automatic-rename {value} for window {pane_id}")
        return True
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'set-option', '-t', pane_id, 'automatic-rename', value], error=str(e))
        logger.error(f"Failed to set automatic-rename for {pane_id}: {e}")
        return False

def set_pane_name(pane_id, name):
    """Set the window name of a tmux pane and disable automatic rename"""
    logger.log_function_call('set_pane_name', args=[pane_id, name])
    try:
        # First disable automatic rename for this window
        set_window_auto_rename(pane_id, False)
        
        # Then set the window name
        cmd = ['tmux', 'rename-window', '-t', pane_id, name]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.log_tmux_command(cmd, "SUCCESS")
        logger.info(f"Set pane {pane_id} window name to: {name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.log_tmux_command(['tmux', 'rename-window', '-t', pane_id, name], error=str(e))
        logger.error(f"Failed to set window name for {pane_id}: {e}")
        return False

def save_pane_state(pane_id, original_name, status):
    """Save pane state to a temporary file"""
    logger.log_function_call('save_pane_state', args=[pane_id, original_name, status])
    state_file = get_script_dir() / f".pane_state_{pane_id.replace('%', '')}.json"
    
    # Get the current auto-rename status to restore later
    auto_rename_was_on = get_window_auto_rename_status(pane_id)
    
    state = {
        'pane_id': pane_id,
        'original_name': original_name,
        'status': status,
        'timestamp': time.time(),
        'auto_rename_was_on': auto_rename_was_on
    }
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f)
        logger.log_pane_state(pane_id, f"SAVED_{status.upper()}", state)
        logger.info(f"Saved state for pane {pane_id}: {status}")
    except IOError as e:
        logger.error(f"Failed to save state for pane {pane_id}: {e}")

def load_pane_state(pane_id):
    """Load pane state from temporary file"""
    logger.log_function_call('load_pane_state', args=[pane_id])
    state_file = get_script_dir() / f".pane_state_{pane_id.replace('%', '')}.json"
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            logger.log_pane_state(pane_id, "LOADED", state)
            logger.debug(f"Loaded state for pane {pane_id}: {state}")
            return state
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load state for pane {pane_id}: {e}")
            return None
    else:
        logger.debug(f"No state file found for pane {pane_id}")
        return None

def cleanup_pane_state(pane_id):
    """Remove pane state file"""
    logger.log_function_call('cleanup_pane_state', args=[pane_id])
    state_file = get_script_dir() / f".pane_state_{pane_id.replace('%', '')}.json"
    if state_file.exists():
        try:
            state_file.unlink()
            logger.log_pane_state(pane_id, "CLEANED_UP")
            logger.info(f"Cleaned up state for pane {pane_id}")
        except OSError as e:
            logger.error(f"Failed to cleanup state for pane {pane_id}: {e}")
    else:
        logger.debug(f"No state file to cleanup for pane {pane_id}")

def get_claude_pane_id():
    """Get the pane ID where Claude is running"""
    logger.log_function_call('get_claude_pane_id')
    
    # First try to get from TMUX_PANE environment variable
    pane_id = os.environ.get('TMUX_PANE')
    if pane_id:
        logger.debug(f"Got pane ID from TMUX_PANE: {pane_id}")
        return pane_id
    
    # Fallback to current pane (for manual testing)
    pane_id = get_current_tmux_pane()
    if pane_id:
        logger.debug(f"Using current pane ID as fallback: {pane_id}")
        return pane_id
    
    logger.error("Could not determine Claude pane ID")
    return None

def handle_stop_hook():
    """Handle Claude stop event - add checkmark emoji"""
    logger.log_function_call('handle_stop_hook')
    logger.info("Processing Claude stop hook")
    
    pane_id = get_claude_pane_id()
    if not pane_id:
        logger.error("Could not get Claude pane ID")
        logger.log_hook_execution('STOP', None, success=False)
        return
    
    current_name = get_pane_name(pane_id)
    if not current_name:
        logger.error(f"Could not get current name for pane {pane_id}")
        logger.log_hook_execution('STOP', pane_id, success=False)
        return
    
    logger.debug(f"Current pane name: {current_name}")
    
    # Check if we already have a state saved
    state = load_pane_state(pane_id)
    if state:
        original_name = state['original_name']
        logger.debug(f"Using saved original name: {original_name}")
    else:
        # Remove any existing emoji prefix to get original name
        original_name = current_name
        for emoji in ['✅', '📢', '❓', '🔄']:
            if original_name.startswith(emoji + ' '):
                original_name = original_name[len(emoji + ' '):]
                logger.debug(f"Removed emoji prefix, original name: {original_name}")
                break
    
    # Set new name with checkmark emoji
    new_name = f"✅ {original_name}"
    logger.debug(f"Setting new name: {new_name}")
    
    if set_pane_name(pane_id, new_name):
        save_pane_state(pane_id, original_name, 'stop')
        
        # Send notification
        session_name = get_current_tmux_session()
        notify_message = f"{session_name}:{pane_id} - Claude finished"
        logger.debug(f"Sending notification: {notify_message}")
        
        logger.log_hook_execution('STOP', pane_id, success=True)
        logger.info(f"Stop hook completed successfully for pane {pane_id}")
    else:
        logger.error(f"Failed to set pane name for {pane_id}")
        logger.log_hook_execution('STOP', pane_id, success=False)

def handle_notification_hook():
    """Handle Claude notification event - add notification emoji"""
    logger.log_function_call('handle_notification_hook')
    logger.info("Processing Claude notification hook")
    
    pane_id = get_claude_pane_id()
    if not pane_id:
        logger.error("Could not get Claude pane ID")
        logger.log_hook_execution('NOTIFICATION', None, success=False)
        return
    
    current_name = get_pane_name(pane_id)
    if not current_name:
        logger.error(f"Could not get current name for pane {pane_id}")
        logger.log_hook_execution('NOTIFICATION', pane_id, success=False)
        return
    
    logger.debug(f"Current pane name: {current_name}")
    
    # Check if we already have a state saved
    state = load_pane_state(pane_id)
    if state:
        original_name = state['original_name']
        logger.debug(f"Using saved original name: {original_name}")
    else:
        # Remove any existing emoji prefix to get original name
        original_name = current_name
        for emoji in ['✅', '📢', '❓', '🔄']:
            if original_name.startswith(emoji + ' '):
                original_name = original_name[len(emoji + ' '):]
                logger.debug(f"Removed emoji prefix, original name: {original_name}")
                break
    
    # Set new name with notification emoji
    new_name = f"📢 {original_name}"
    logger.debug(f"Setting new name: {new_name}")
    
    if set_pane_name(pane_id, new_name):
        save_pane_state(pane_id, original_name, 'notification')
        
        # Send notification
        session_name = get_current_tmux_session()
        notify_message = f"{session_name}:{pane_id} - Claude notification"
        logger.debug(f"Sending notification: {notify_message}")
        
        logger.log_hook_execution('NOTIFICATION', pane_id, success=True)
        logger.info(f"Notification hook completed successfully for pane {pane_id}")
    else:
        logger.error(f"Failed to set pane name for {pane_id}")
        logger.log_hook_execution('NOTIFICATION', pane_id, success=False)

def is_waiting_for_permission():
    """
    Determine if Claude is waiting for user permission by analyzing the hook payload.
    
    This function attempts to detect if Claude is in a permission-waiting state
    by examining various indicators in the environment and system state.
    """
    logger.log_function_call('is_waiting_for_permission')
    
    try:
        # Try to read JSON payload from stdin (if available)
        import select
        import sys
        
        # Check if there's input available on stdin
        if select.select([sys.stdin], [], [], 0.1)[0]:
            try:
                payload_data = sys.stdin.read()
                if payload_data:
                    payload = json.loads(payload_data)
                    logger.debug(f"Received hook payload: {payload}")
                    
                    # Log the tool being called for debugging
                    tool_name = payload.get('tool_name', 'unknown')
                    logger.debug(f"Tool being called: {tool_name}")
                    
                    # For now, we'll use a heuristic approach
                    # Claude typically waits for permission on potentially dangerous tools
                    # or when the user has not granted blanket permission
                    
                    # Check if this is a tool that typically requires permission
                    permission_required_tools = ['Bash', 'Write', 'Edit', 'MultiEdit']
                    if tool_name in permission_required_tools:
                        logger.debug(f"Tool {tool_name} typically requires permission")
                        return True
                    
                    # Additional heuristics could be added here based on:
                    # - Tool parameters (e.g., dangerous commands in Bash)
                    # - Session state
                    # - User preferences
                    
                    return False
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Could not parse hook payload: {e}")
                
        # Fallback: use environment variables or other indicators
        # Check if we're in a permission-waiting state by looking for specific env vars
        # or checking recent tool execution patterns
        
        # For now, we'll be conservative and assume permission is needed
        # This can be refined based on actual usage patterns
        logger.debug("No payload available, using fallback heuristics")
        return True
        
    except Exception as e:
        logger.error(f"Error in permission detection: {e}")
        return False

def handle_pretooluse_hook():
    """Handle Claude PreToolUse event - add question mark emoji only when waiting for permission"""
    logger.log_function_call('handle_pretooluse_hook')
    logger.info("Processing Claude PreToolUse hook")
    
    # First, determine if Claude is actually waiting for permission
    if not is_waiting_for_permission():
        logger.debug("Claude is not waiting for permission, skipping emoji display")
        logger.log_hook_execution('PRETOOLUSE', None, success=True)
        return
    
    logger.info("Claude is waiting for permission, showing question mark emoji")
    
    pane_id = get_claude_pane_id()
    if not pane_id:
        logger.error("Could not get Claude pane ID")
        logger.log_hook_execution('PRETOOLUSE', None, success=False)
        return
    
    current_name = get_pane_name(pane_id)
    if not current_name:
        logger.error(f"Could not get current name for pane {pane_id}")
        logger.log_hook_execution('PRETOOLUSE', pane_id, success=False)
        return
    
    logger.debug(f"Current pane name: {current_name}")
    
    # Check if we already have a state saved
    state = load_pane_state(pane_id)
    if state:
        original_name = state['original_name']
        logger.debug(f"Using saved original name: {original_name}")
    else:
        # Remove any existing emoji prefix to get original name
        original_name = current_name
        for emoji in ['✅', '📢', '❓', '🔄']:
            if original_name.startswith(emoji + ' '):
                original_name = original_name[len(emoji + ' '):]
                logger.debug(f"Removed emoji prefix, original name: {original_name}")
                break
    
    # Set new name with question mark emoji
    new_name = f"❓ {original_name}"
    logger.debug(f"Setting new name: {new_name}")
    
    if set_pane_name(pane_id, new_name):
        save_pane_state(pane_id, original_name, 'permission')
        
        # Send notification
        session_name = get_current_tmux_session()
        notify_message = f"{session_name}:{pane_id} - Claude needs tool permission"
        logger.debug(f"Sending notification: {notify_message}")
        
        logger.log_hook_execution('PRETOOLUSE', pane_id, success=True)
        logger.info(f"PreToolUse hook completed successfully for pane {pane_id}")
    else:
        logger.error(f"Failed to set pane name for {pane_id}")
        logger.log_hook_execution('PRETOOLUSE', pane_id, success=False)

def restore_pane_name(pane_id):
    """Restore original pane name and auto-rename setting"""
    logger.log_function_call('restore_pane_name', args=[pane_id])
    logger.info(f"Restoring original name for pane {pane_id}")
    
    state = load_pane_state(pane_id)
    if state:
        original_name = state['original_name']
        auto_rename_was_on = state.get('auto_rename_was_on', True)
        logger.debug(f"Restoring to original name: {original_name}, auto-rename: {auto_rename_was_on}")
        
        # Restore the window name
        try:
            cmd = ['tmux', 'rename-window', '-t', pane_id, original_name]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.log_tmux_command(cmd, "SUCCESS")
            logger.info(f"Restored pane {pane_id} window name to: {original_name}")
            
            # Restore the auto-rename setting
            if set_window_auto_rename(pane_id, auto_rename_was_on):
                logger.debug(f"Restored auto-rename setting for pane {pane_id}")
            
            cleanup_pane_state(pane_id)
            logger.info(f"Successfully restored pane {pane_id} to original state")
            return True
        except subprocess.CalledProcessError as e:
            logger.log_tmux_command(['tmux', 'rename-window', '-t', pane_id, original_name], error=str(e))
            logger.error(f"Failed to restore pane {pane_id} name: {e}")
            return False
    else:
        logger.warning(f"No state found for pane {pane_id} to restore")
        return False

def clear_emoji_on_enter():
    """Clear emoji prefix from current pane when Enter is pressed"""
    logger.log_function_call('clear_emoji_on_enter')
    
    # Get current pane ID
    pane_id = get_current_tmux_pane()
    if not pane_id:
        logger.debug("Could not get current pane ID for Enter key clear")
        return
    
    # Check if this pane has an emoji prefix (saved state exists)
    state = load_pane_state(pane_id)
    if state:
        logger.debug(f"Found emoji state for pane {pane_id}, clearing emoji prefix")
        restore_pane_name(pane_id)
    else:
        logger.debug(f"No emoji state found for pane {pane_id}, no action needed")
    
    # This function is designed to be lightweight and fast
    # to avoid introducing input lag when Enter is pressed

def main():
    if len(sys.argv) < 2:
        print("Usage: claude_tmux_hooks.py [stop|notification|pretooluse|restore|clear_emoji_on_enter] [pane_id]")
        sys.exit(1)
    
    action = sys.argv[1]
    logger.info(f"Starting claude_tmux_hooks with action: {action}")
    logger.debug(f"Command line args: {sys.argv}")
    
    try:
        if action == 'stop':
            handle_stop_hook()
        elif action == 'notification':
            handle_notification_hook()
        elif action == 'pretooluse':
            handle_pretooluse_hook()
        elif action == 'restore':
            if len(sys.argv) >= 3:
                pane_id = sys.argv[2]
                restore_pane_name(pane_id)
            else:
                pane_id = get_claude_pane_id()
                if pane_id:
                    restore_pane_name(pane_id)
                else:
                    logger.error("Could not get Claude pane ID for restore")
        elif action == 'clear_emoji_on_enter':
            clear_emoji_on_enter()
        else:
            logger.error(f"Unknown action: {action}")
            print(f"Unknown action: {action}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        raise

if __name__ == '__main__':
    main()
