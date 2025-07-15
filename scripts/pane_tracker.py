#!/usr/bin/env python3

import os
import sys
import time
import json
import threading
import signal
from pathlib import Path
from tmux_integration import TmuxIntegration
from claude_tmux_hooks import restore_pane_name, load_pane_state

class PaneTracker:
    def __init__(self):
        self.tmux = TmuxIntegration()
        self.script_dir = Path(__file__).parent
        self.tracker_file = self.script_dir / '.pane_tracker.json'
        self.running = False
        self.monitor_thread = None
        
    def load_tracked_panes(self):
        """Load the list of tracked panes from file"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_tracked_panes(self, tracked_panes):
        """Save the list of tracked panes to file"""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(tracked_panes, f, indent=2)
        except IOError:
            pass
    
    def add_tracked_pane(self, pane_id, session_name):
        """Add a pane to the tracked list"""
        tracked_panes = self.load_tracked_panes()
        tracked_panes[pane_id] = {
            'session_name': session_name,
            'last_activity': time.time(),
            'status': 'active'
        }
        self.save_tracked_panes(tracked_panes)
    
    def remove_tracked_pane(self, pane_id):
        """Remove a pane from the tracked list"""
        tracked_panes = self.load_tracked_panes()
        if pane_id in tracked_panes:
            del tracked_panes[pane_id]
            self.save_tracked_panes(tracked_panes)
    
    def update_pane_activity(self, pane_id):
        """Update the last activity time for a pane"""
        tracked_panes = self.load_tracked_panes()
        if pane_id in tracked_panes:
            tracked_panes[pane_id]['last_activity'] = time.time()
            self.save_tracked_panes(tracked_panes)
    
    def monitor_pane_activity(self, pane_id):
        """Monitor a specific pane for user activity and restore name when active"""
        # This is called when a pane becomes active
        self.update_pane_activity(pane_id)
        
        # Check if this pane has a saved state (emoji prefix)
        state = load_pane_state(pane_id)
        if state:
            # Restore the original name when user becomes active
            restore_pane_name(pane_id)
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Clean up dead panes
                self.cleanup_dead_panes()
                
                # Check for inactive panes and clean up old states
                self.cleanup_old_states()
                
                time.sleep(30)  # Check every 30 seconds
            except Exception:
                pass
    
    def cleanup_dead_panes(self):
        """Remove tracking for panes that no longer exist"""
        tracked_panes = self.load_tracked_panes()
        current_panes = {pane['pane_id'] for pane in self.tmux.get_all_panes()}
        
        # Remove dead panes
        dead_panes = []
        for pane_id in tracked_panes:
            if pane_id not in current_panes:
                dead_panes.append(pane_id)
        
        if dead_panes:
            for pane_id in dead_panes:
                del tracked_panes[pane_id]
                # Also clean up state files
                try:
                    state_file = self.script_dir / f".pane_state_{pane_id.replace('%', '')}.json"
                    if state_file.exists():
                        state_file.unlink()
                except Exception:
                    pass
            
            self.save_tracked_panes(tracked_panes)
    
    def cleanup_old_states(self):
        """Clean up state files for panes that haven't been active recently"""
        current_time = time.time()
        max_age = 3600  # 1 hour
        
        for state_file in self.script_dir.glob('.pane_state_*.json'):
            try:
                if current_time - state_file.stat().st_mtime > max_age:
                    state_file.unlink()
            except Exception:
                pass
    
    def handle_pane_exit(self, pane_id):
        """Handle when a pane exits"""
        self.remove_tracked_pane(pane_id)
        
        # Clean up state file
        try:
            state_file = self.script_dir / f".pane_state_{pane_id.replace('%', '')}.json"
            if state_file.exists():
                state_file.unlink()
        except Exception:
            pass
    
    def get_tracked_panes_status(self):
        """Get status of all tracked panes"""
        tracked_panes = self.load_tracked_panes()
        current_panes = {pane['pane_id']: pane for pane in self.tmux.get_all_panes()}
        
        status = {}
        for pane_id, info in tracked_panes.items():
            if pane_id in current_panes:
                pane_info = current_panes[pane_id]
                state = load_pane_state(pane_id)
                
                status[pane_id] = {
                    'title': pane_info['title'],
                    'session': info['session_name'],
                    'last_activity': info['last_activity'],
                    'has_emoji': state is not None,
                    'emoji_status': state['status'] if state else None
                }
        
        return status

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    if len(sys.argv) < 2:
        print("Usage: pane_tracker.py [monitor|cleanup|status] [pane_id]")
        sys.exit(1)
    
    tracker = PaneTracker()
    command = sys.argv[1]
    
    if command == 'monitor':
        if len(sys.argv) >= 3:
            pane_id = sys.argv[2]
            tracker.monitor_pane_activity(pane_id)
        else:
            # Start general monitoring
            tracker.start_monitoring()
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                tracker.stop_monitoring()
    
    elif command == 'cleanup':
        if len(sys.argv) >= 3:
            pane_id = sys.argv[2]
            tracker.handle_pane_exit(pane_id)
        else:
            tracker.cleanup_dead_panes()
    
    elif command == 'status':
        status = tracker.get_tracked_panes_status()
        print(json.dumps(status, indent=2))
    
    elif command == 'add':
        if len(sys.argv) >= 4:
            pane_id = sys.argv[2]
            session_name = sys.argv[3]
            tracker.add_tracked_pane(pane_id, session_name)
    
    elif command == 'remove':
        if len(sys.argv) >= 3:
            pane_id = sys.argv[2]
            tracker.remove_tracked_pane(pane_id)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()