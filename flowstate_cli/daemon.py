import os
import sys
import json
import time
import signal
import threading
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from plyer import notification
from flowstate_cli.config import config

class TimerDaemon:
    def __init__(self):
        self.config_dir = Path.home() / ".flowstate"
        self.state_file = self.config_dir / "timer_state.json"
        self.pid_file = self.config_dir / "timer.pid"
        self.config_dir.mkdir(exist_ok=True)
        
        self.active = False
        self.paused = False
        self.start_time: Optional[float] = None
        self.duration_seconds: int = 0
        self.remaining_seconds: int = 0
        self.session_type: str = ""
        self.task_description: str = ""
        self.task_id: Optional[int] = None
        
        # Load state if daemon is running
        self._load_state()
    
    def _save_state(self):
        """Save timer state to file"""
        state = {
            "active": self.active,
            "paused": self.paused,
            "start_time": self.start_time,
            "duration_seconds": self.duration_seconds,
            "remaining_seconds": self.remaining_seconds,
            "session_type": self.session_type,
            "task_description": self.task_description,
            "task_id": self.task_id,
            "last_update": time.time()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load timer state from file"""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.active = state.get("active", False)
            self.paused = state.get("paused", False)
            self.start_time = state.get("start_time")
            self.duration_seconds = state.get("duration_seconds", 0)
            self.remaining_seconds = state.get("remaining_seconds", 0)
            self.session_type = state.get("session_type", "")
            self.task_description = state.get("task_description", "")
            self.task_id = state.get("task_id")
            
            # Update remaining time based on elapsed time
            if self.active and self.start_time:
                elapsed = time.time() - self.start_time
                if not self.paused:
                    self.remaining_seconds = max(0, self.duration_seconds - int(elapsed))
                    if self.remaining_seconds <= 0:
                        self.active = False
                        self._on_timer_complete()
        except Exception:
            # If state file is corrupted, start fresh
            self._clear_state()
    
    def _clear_state(self):
        """Clear timer state"""
        self.active = False
        self.paused = False
        self.start_time = None
        self.duration_seconds = 0
        self.remaining_seconds = 0
        self.session_type = ""
        self.task_description = ""
        self.task_id = None
        
        if self.state_file.exists():
            self.state_file.unlink()
    
    def is_daemon_running(self) -> bool:
        """Check if daemon process is running"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            os.kill(pid, 0)  # This will raise an exception if process doesn't exist
            return True
        except (ValueError, OSError, ProcessLookupError):
            # PID file exists but process is dead, clean up
            self.pid_file.unlink()
            return False
    
    def start_daemon(self):
        """Start the daemon process in the background"""
        if self.is_daemon_running():
            return False, "Timer daemon is already running"
        
        # Use subprocess to start daemon in background
        script_path = Path(__file__).parent / "daemon_runner.py"
        if platform.system() == "Windows":
            # Windows subprocess
            subprocess.Popen([
                sys.executable, str(script_path)
            ], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            # Unix-like systems
            subprocess.Popen([
                sys.executable, str(script_path)
            ], start_new_session=True)
        
        # Give daemon time to start
        time.sleep(1)
        
        if self.is_daemon_running():
            return True, "Timer daemon started"
        else:
            return False, "Failed to start timer daemon"
    
    def stop_daemon(self):
        """Stop the daemon process"""
        if not self.is_daemon_running():
            return False, "No timer daemon is running"
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            if platform.system() == "Windows":
                # Windows doesn't have SIGTERM, use SIGINT
                os.kill(pid, signal.SIGINT)
            else:
                os.kill(pid, signal.SIGTERM)
            
            time.sleep(0.5)  # Give it time to clean up
            
            # Clean up files
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            return True, "Timer daemon stopped"
        except Exception as e:
            return False, f"Failed to stop daemon: {e}"
    
    def start_timer(self, duration_minutes: int, session_type: str, task_description: str = "", task_id: Optional[int] = None):
        """Start a timer session"""
        # Ensure daemon is running
        if not self.is_daemon_running():
            success, message = self.start_daemon()
            if not success:
                return False, message
            time.sleep(1)  # Give daemon time to start
        
        # Check if timer is already active
        self._load_state()
        if self.active:
            return False, "Timer is already running"
        
        # Set timer parameters
        self.duration_seconds = duration_minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.session_type = session_type
        self.task_description = task_description
        self.task_id = task_id
        self.active = True
        self.paused = False
        self.start_time = time.time()
        
        self._save_state()
        return True, f"Started {session_type} timer for {duration_minutes} minutes"
    
    def stop_timer(self):
        """Stop the current timer"""
        self._load_state()
        if not self.active:
            return False, "No timer is running"
        
        self.active = False
        self.paused = False
        self._save_state()
        return True, "Timer stopped"
    
    def pause_timer(self):
        """Pause/resume the current timer"""
        self._load_state()
        if not self.active:
            return False, "No timer is running"
        
        self.paused = not self.paused
        if self.paused:
            # Record pause time
            elapsed = time.time() - self.start_time
            self.remaining_seconds = max(0, self.duration_seconds - int(elapsed))
        else:
            # Resume - reset start time
            self.start_time = time.time()
            self.duration_seconds = self.remaining_seconds
        
        self._save_state()
        status = "paused" if self.paused else "resumed"
        return True, f"Timer {status}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current timer status"""
        self._load_state()
        
        if not self.active:
            return {"active": False, "daemon_running": self.is_daemon_running()}
        
        # Update remaining time for active non-paused timers
        if not self.paused and self.start_time:
            elapsed = time.time() - self.start_time
            self.remaining_seconds = max(0, self.duration_seconds - int(elapsed))
        
        return {
            "active": True,
            "paused": self.paused,
            "session_type": self.session_type,
            "task_description": self.task_description,
            "task_id": self.task_id,
            "remaining_seconds": self.remaining_seconds,
            "remaining_minutes": self.remaining_seconds // 60,
            "remaining_display": self._format_time(self.remaining_seconds),
            "daemon_running": self.is_daemon_running()
        }
    
    def _on_timer_complete(self):
        """Handle timer completion"""
        # Play notification sound
        if config.get("sound_enabled", True):
            self._play_notification_sound()
        
        # Show desktop notification
        if config.get("notifications_enabled", True):
            self._show_notification()
    
    def _play_notification_sound(self):
        """Play notification sound"""
        try:
            system = platform.system().lower()
            if system == "darwin":  # macOS
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                             check=False, capture_output=True)
            elif system == "linux":
                subprocess.run(["paplay", "/usr/share/sounds/alsa/Front_Left.wav"], 
                             check=False, capture_output=True)
        except Exception:
            pass
    
    def _show_notification(self):
        """Show desktop notification"""
        try:
            title = "FlowState"
            
            if self.session_type == "focus":
                message = "Pomodoro finished! Time for a break."
            elif self.session_type == "short_break":
                message = "Short break over. Time to focus!"
            elif self.session_type == "long_break":
                message = "Long break over. Time to focus!"
            else:
                message = f"{self.session_type.title()} session completed!"
            
            notification.notify(
                title=title,
                message=message,
                timeout=5
            )
        except Exception:
            pass
    
    def _format_time(self, seconds: int) -> str:
        """Format time as MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

# Global daemon instance
daemon = TimerDaemon()
