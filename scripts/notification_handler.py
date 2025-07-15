#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from tmux_integration import TmuxIntegration

class NotificationHandler:
    def __init__(self):
        self.tmux = TmuxIntegration()
        self.script_dir = Path(__file__).parent
        
    def send_notification(self, message, priority='normal'):
        """Send a notification using notify_windows command"""
        try:
            # Use the notify_windows command as specified in CLAUDE.md
            subprocess.run(['notify_windows', message], check=False)
            return True
        except FileNotFoundError:
            # Fallback to system notifications if notify_windows is not available
            return self._send_system_notification(message, priority)
        except Exception:
            return False
    
    def _send_system_notification(self, message, priority='normal'):
        """Fallback to system notification methods"""
        # Try notify-send (Linux)
        try:
            urgency = 'normal'
            if priority == 'high':
                urgency = 'critical'
            elif priority == 'low':
                urgency = 'low'
            
            subprocess.run(['notify-send', '-u', urgency, 'Claude Tmux', message], 
                          check=False, capture_output=True)
            return True
        except FileNotFoundError:
            pass
        
        # Try osascript (macOS)
        try:
            script = f'display notification "{message}" with title "Claude Tmux"'
            subprocess.run(['osascript', '-e', script], 
                          check=False, capture_output=True)
            return True
        except FileNotFoundError:
            pass
        
        # Try Windows toast notifications
        try:
            # Simple Windows notification using powershell
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText01
            $toastXml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
            $toastXml.SelectSingleNode("//text[@id='1']").AppendChild($toastXml.CreateTextNode("{message}")) | Out-Null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Tmux").Show($toast)
            '''
            subprocess.run(['powershell', '-Command', ps_script], 
                          check=False, capture_output=True)
            return True
        except FileNotFoundError:
            pass
        
        return False
    
    def format_pane_notification(self, pane_id, event_type, session_name=None):
        """Format a notification message for a pane event"""
        if not session_name:
            session_name = self.tmux.get_current_session() or 'unknown'
        
        pane_info = self.tmux.get_pane_info(pane_id)
        pane_title = pane_info['title'] if pane_info else 'unknown'
        
        # Remove emoji prefixes from title for cleaner notification
        clean_title = pane_title
        for emoji in ['✅', '📢', '🔄']:
            if clean_title.startswith(emoji + ' '):
                clean_title = clean_title[len(emoji + ' '):]
                break
        
        if event_type == 'stop':
            emoji = '✅'
            action = 'finished'
        elif event_type == 'notification':
            emoji = '📢'
            action = 'sent notification'
        else:
            emoji = '🔄'
            action = event_type
        
        # Format as specified in CLAUDE.md: prepend with pane name
        message = f"{session_name}:{pane_id} - Claude {action}"
        return message
    
    def notify_claude_stop(self, pane_id=None, session_name=None):
        """Send notification when Claude stops"""
        if not pane_id:
            pane_id = self.tmux.get_current_pane()
        
        if pane_id:
            message = self.format_pane_notification(pane_id, 'stop', session_name)
            return self.send_notification(message)
        return False
    
    def notify_claude_notification(self, pane_id=None, session_name=None):
        """Send notification when Claude sends a notification"""
        if not pane_id:
            pane_id = self.tmux.get_current_pane()
        
        if pane_id:
            message = self.format_pane_notification(pane_id, 'notification', session_name)
            return self.send_notification(message, priority='high')
        return False
    
    def notify_custom(self, message, pane_id=None, session_name=None):
        """Send a custom notification with pane prefix"""
        if not pane_id:
            pane_id = self.tmux.get_current_pane()
        
        if not session_name:
            session_name = self.tmux.get_current_session() or 'unknown'
        
        if pane_id:
            formatted_message = f"{session_name}:{pane_id} - {message}"
            return self.send_notification(formatted_message)
        else:
            return self.send_notification(message)
    
    def test_notification_system(self):
        """Test the notification system"""
        methods = []
        
        # Test notify_windows
        try:
            result = subprocess.run(['notify_windows', 'Test notification'], 
                                  check=False, capture_output=True)
            methods.append(f"notify_windows: {'✅' if result.returncode == 0 else '❌'}")
        except FileNotFoundError:
            methods.append("notify_windows: ❌ (not found)")
        
        # Test notify-send
        try:
            result = subprocess.run(['notify-send', 'Test', 'Test notification'], 
                                  check=False, capture_output=True)
            methods.append(f"notify-send: {'✅' if result.returncode == 0 else '❌'}")
        except FileNotFoundError:
            methods.append("notify-send: ❌ (not found)")
        
        # Test osascript
        try:
            result = subprocess.run(['osascript', '-e', 'display notification "Test" with title "Test"'], 
                                  check=False, capture_output=True)
            methods.append(f"osascript: {'✅' if result.returncode == 0 else '❌'}")
        except FileNotFoundError:
            methods.append("osascript: ❌ (not found)")
        
        return methods

def main():
    if len(sys.argv) < 2:
        print("Usage: notification_handler.py [stop|notification|custom|test] [args...]")
        sys.exit(1)
    
    handler = NotificationHandler()
    command = sys.argv[1]
    
    if command == 'stop':
        pane_id = sys.argv[2] if len(sys.argv) >= 3 else None
        session_name = sys.argv[3] if len(sys.argv) >= 4 else None
        success = handler.notify_claude_stop(pane_id, session_name)
        print("OK" if success else "FAILED")
    
    elif command == 'notification':
        pane_id = sys.argv[2] if len(sys.argv) >= 3 else None
        session_name = sys.argv[3] if len(sys.argv) >= 4 else None
        success = handler.notify_claude_notification(pane_id, session_name)
        print("OK" if success else "FAILED")
    
    elif command == 'custom':
        if len(sys.argv) >= 3:
            message = sys.argv[2]
            pane_id = sys.argv[3] if len(sys.argv) >= 4 else None
            session_name = sys.argv[4] if len(sys.argv) >= 5 else None
            success = handler.notify_custom(message, pane_id, session_name)
            print("OK" if success else "FAILED")
        else:
            print("Usage: notification_handler.py custom <message> [pane_id] [session_name]")
            sys.exit(1)
    
    elif command == 'test':
        print("Testing notification methods:")
        methods = handler.test_notification_system()
        for method in methods:
            print(f"  {method}")
        
        # Send a test notification
        print("\nSending test notification...")
        success = handler.send_notification("Test notification from Claude Tmux plugin")
        print(f"Test result: {'✅' if success else '❌'}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()