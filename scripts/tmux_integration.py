#!/usr/bin/env python3

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from debug_logger import DebugLogger

class TmuxIntegration:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.logger = DebugLogger('tmux_integration')
    
    def run_tmux_command(self, args: List[str]) -> Optional[str]:
        """Run a tmux command and return output"""
        self.logger.log_function_call('run_tmux_command', args=[args])
        try:
            cmd = ['tmux'] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            self.logger.log_tmux_command(cmd, output)
            return output
        except subprocess.CalledProcessError as e:
            self.logger.log_tmux_command(['tmux'] + args, error=str(e))
            self.logger.error(f"Tmux command failed: {e}")
            return None
    
    def get_all_panes(self) -> List[Dict]:
        """Get information about all tmux panes"""
        panes = []
        output = self.run_tmux_command(['list-panes', '-a', '-F', 
                                       '#{session_name}:#{window_index}.#{pane_index}:#{pane_id}:#{pane_title}:#{pane_pid}'])
        if output:
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split(':')
                    if len(parts) >= 5:
                        panes.append({
                            'session_window_pane': parts[0],
                            'pane_id': parts[1],
                            'title': ':'.join(parts[2:-1]),  # Handle colons in title
                            'pid': parts[-1]
                        })
        return panes
    
    def get_pane_info(self, pane_id: str) -> Optional[Dict]:
        """Get detailed information about a specific pane"""
        output = self.run_tmux_command(['display-message', '-p', '-t', pane_id,
                                       '#{session_name}:#{window_index}.#{pane_index}:#{pane_id}:#{pane_title}:#{pane_pid}'])
        if output:
            parts = output.split(':')
            if len(parts) >= 5:
                return {
                    'session_window_pane': parts[0],
                    'pane_id': parts[1],
                    'title': ':'.join(parts[2:-1]),
                    'pid': parts[-1]
                }
        return None
    
    def get_pane_title(self, pane_id: str) -> Optional[str]:
        """Get the window name of a specific pane"""
        return self.run_tmux_command(['display-message', '-p', '-t', pane_id, '#{window_name}'])
    
    def set_pane_title(self, pane_id: str, title: str) -> bool:
        """Set the window name of a specific pane"""
        try:
            subprocess.run(['tmux', 'rename-window', '-t', pane_id, title], 
                          check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_pane(self) -> Optional[str]:
        """Get the current pane ID"""
        return self.run_tmux_command(['display-message', '-p', '#{pane_id}'])
    
    def get_current_session(self) -> Optional[str]:
        """Get the current session name"""
        return self.run_tmux_command(['display-message', '-p', '#{session_name}'])
    
    def is_pane_active(self, pane_id: str) -> bool:
        """Check if a pane is currently active"""
        current_pane = self.get_current_pane()
        return current_pane == pane_id
    
    def find_claude_panes(self) -> List[Dict]:
        """Find panes that might be running Claude"""
        claude_panes = []
        panes = self.get_all_panes()
        
        for pane in panes:
            # Check if the pane process tree contains claude
            try:
                # Get process tree for this pane
                result = subprocess.run(['pstree', '-p', pane['pid']], 
                                      capture_output=True, text=True, check=False)
                if result.returncode == 0 and 'claude' in result.stdout.lower():
                    claude_panes.append(pane)
            except FileNotFoundError:
                # pstree not available, fall back to ps
                try:
                    result = subprocess.run(['ps', '-p', pane['pid'], '-o', 'comm='], 
                                          capture_output=True, text=True, check=False)
                    if result.returncode == 0 and 'claude' in result.stdout.lower():
                        claude_panes.append(pane)
                except Exception:
                    pass
        
        return claude_panes
    
    def monitor_pane_activity(self, pane_id: str, callback_script: str):
        """Set up monitoring for pane activity"""
        # Use tmux hooks to monitor when the pane becomes active
        hook_command = f"run-shell '{callback_script} {pane_id}'"
        
        # Monitor when this pane is selected
        try:
            subprocess.run(['tmux', 'set-hook', '-t', pane_id, 'after-select-pane', hook_command], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass
    
    def remove_pane_monitoring(self, pane_id: str):
        """Remove monitoring for a specific pane"""
        try:
            subprocess.run(['tmux', 'set-hook', '-t', pane_id, '-u', 'after-select-pane'], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass
    
    def cleanup_dead_panes(self):
        """Clean up state files for panes that no longer exist"""
        current_panes = {pane['pane_id'] for pane in self.get_all_panes()}
        
        # Find and remove state files for dead panes
        for state_file in self.script_dir.glob('.pane_state_*.json'):
            try:
                pane_id = state_file.stem.replace('.pane_state_', '')
                pane_id = f"%{pane_id}"
                
                if pane_id not in current_panes:
                    state_file.unlink()
            except Exception:
                pass

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: tmux_integration.py [command] [args...]")
        sys.exit(1)
    
    tmux = TmuxIntegration()
    command = sys.argv[1]
    
    if command == 'list-panes':
        panes = tmux.get_all_panes()
        for pane in panes:
            print(f"{pane['pane_id']}: {pane['title']} (PID: {pane['pid']})")
    
    elif command == 'find-claude':
        claude_panes = tmux.find_claude_panes()
        for pane in claude_panes:
            print(f"{pane['pane_id']}: {pane['title']} (PID: {pane['pid']})")
    
    elif command == 'get-title':
        if len(sys.argv) >= 3:
            pane_id = sys.argv[2]
            title = tmux.get_pane_title(pane_id)
            if title:
                print(title)
    
    elif command == 'set-title':
        if len(sys.argv) >= 4:
            pane_id = sys.argv[2]
            title = sys.argv[3]
            success = tmux.set_pane_title(pane_id, title)
            print("OK" if success else "FAILED")
    
    elif command == 'current-pane':
        pane_id = tmux.get_current_pane()
        if pane_id:
            print(pane_id)
    
    elif command == 'cleanup':
        tmux.cleanup_dead_panes()
        print("Cleanup completed")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()