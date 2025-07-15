#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

class DebugLogger:
    def __init__(self, script_name):
        self.script_dir = Path(__file__).parent
        self.log_dir = self.script_dir / '.logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Create log file for this script
        self.log_file = self.log_dir / f'{script_name}.log'
        self.main_log_file = self.log_dir / 'tmux_claude.log'
        
        # Check if debug is enabled
        self.debug_enabled = self._is_debug_enabled()
        
        if self.debug_enabled:
            self._setup_logger(script_name)
    
    def _is_debug_enabled(self):
        """Check if debug logging is enabled via environment variable or config"""
        # Check environment variable
        if os.environ.get('TMUX_CLAUDE_DEBUG', '').lower() in ('1', 'true', 'yes'):
            return True
        
        # Check config file
        config_file = self.script_dir / '.debug_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('debug_enabled', False)
            except (json.JSONDecodeError, IOError):
                pass
        
        return False
    
    def _setup_logger(self, script_name):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger(f'tmux_claude_{script_name}')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for script-specific logs
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # File handler for main log
        main_handler = logging.FileHandler(self.main_log_file, mode='a')
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(formatter)
        self.logger.addHandler(main_handler)
        
        # Console handler if stderr is available
        if sys.stderr.isatty():
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message, **kwargs):
        """Log debug message"""
        if self.debug_enabled:
            extra_info = f" | {json.dumps(kwargs)}" if kwargs else ""
            self.logger.debug(f"{message}{extra_info}")
    
    def info(self, message, **kwargs):
        """Log info message"""
        if self.debug_enabled:
            extra_info = f" | {json.dumps(kwargs)}" if kwargs else ""
            self.logger.info(f"{message}{extra_info}")
    
    def warning(self, message, **kwargs):
        """Log warning message"""
        if self.debug_enabled:
            extra_info = f" | {json.dumps(kwargs)}" if kwargs else ""
            self.logger.warning(f"{message}{extra_info}")
    
    def error(self, message, **kwargs):
        """Log error message"""
        if self.debug_enabled:
            extra_info = f" | {json.dumps(kwargs)}" if kwargs else ""
            self.logger.error(f"{message}{extra_info}")
    
    def log_function_call(self, func_name, args=None, kwargs=None):
        """Log function call with arguments"""
        if self.debug_enabled:
            args_str = f"args={args}" if args else ""
            kwargs_str = f"kwargs={kwargs}" if kwargs else ""
            separator = ", " if args_str and kwargs_str else ""
            self.debug(f"CALL {func_name}({args_str}{separator}{kwargs_str})")
    
    def log_tmux_command(self, command, result=None, error=None):
        """Log tmux command execution"""
        if self.debug_enabled:
            self.debug(f"TMUX_CMD: {' '.join(command)}")
            if result:
                self.debug(f"TMUX_OUT: {result}")
            if error:
                self.error(f"TMUX_ERR: {error}")
    
    def log_pane_state(self, pane_id, action, state=None):
        """Log pane state changes"""
        if self.debug_enabled:
            self.info(f"PANE {pane_id} {action}", state=state)
    
    def log_hook_execution(self, hook_type, pane_id, success=True):
        """Log hook execution"""
        if self.debug_enabled:
            status = "SUCCESS" if success else "FAILED"
            self.info(f"HOOK {hook_type} {status}", pane_id=pane_id)
    
    def get_log_stats(self):
        """Get logging statistics"""
        if not self.debug_enabled:
            return {"debug_enabled": False}
        
        stats = {
            "debug_enabled": True,
            "log_files": {},
            "total_size": 0
        }
        
        for log_file in self.log_dir.glob('*.log'):
            try:
                stat = log_file.stat()
                stats["log_files"][log_file.name] = {
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                stats["total_size"] += stat.st_size
            except OSError:
                pass
        
        return stats

def enable_debug():
    """Enable debug logging"""
    script_dir = Path(__file__).parent
    config_file = script_dir / '.debug_config.json'
    
    config = {"debug_enabled": True}
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Debug logging enabled. Logs will be written to: {script_dir / '.logs'}")

def disable_debug():
    """Disable debug logging"""
    script_dir = Path(__file__).parent
    config_file = script_dir / '.debug_config.json'
    
    if config_file.exists():
        config = {"debug_enabled": False}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    print("Debug logging disabled.")

def view_logs(script_name=None, lines=50):
    """View recent log entries"""
    script_dir = Path(__file__).parent
    log_dir = script_dir / '.logs'
    
    if not log_dir.exists():
        print("No logs directory found.")
        return
    
    if script_name:
        log_file = log_dir / f'{script_name}.log'
        if not log_file.exists():
            print(f"No log file found for {script_name}")
            return
        log_files = [log_file]
    else:
        log_files = sorted(log_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for log_file in log_files:
        print(f"\n=== {log_file.name} ===")
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                for line in recent_lines:
                    print(line.rstrip())
        except IOError as e:
            print(f"Error reading {log_file}: {e}")

def clear_logs():
    """Clear all log files"""
    script_dir = Path(__file__).parent
    log_dir = script_dir / '.logs'
    
    if not log_dir.exists():
        print("No logs directory found.")
        return
    
    count = 0
    for log_file in log_dir.glob('*.log'):
        try:
            log_file.unlink()
            count += 1
        except OSError:
            pass
    
    print(f"Cleared {count} log files.")

def main():
    if len(sys.argv) < 2:
        print("Usage: debug_logger.py [enable|disable|view|clear|stats] [options]")
        print("  enable          - Enable debug logging")
        print("  disable         - Disable debug logging")
        print("  view [script]   - View logs (optionally for specific script)")
        print("  clear           - Clear all log files")
        print("  stats           - Show logging statistics")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'enable':
        enable_debug()
    elif command == 'disable':
        disable_debug()
    elif command == 'view':
        script_name = sys.argv[2] if len(sys.argv) >= 3 else None
        view_logs(script_name)
    elif command == 'clear':
        clear_logs()
    elif command == 'stats':
        logger = DebugLogger('stats')
        stats = logger.get_log_stats()
        print(json.dumps(stats, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()