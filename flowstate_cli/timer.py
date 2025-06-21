import asyncio
import time
import threading
import subprocess
import platform
from typing import Optional
from plyer import notification
from flowstate_cli.config import config

class Timer:
    def __init__(self):
        self.active = False
        self.paused = False
        self.start_time: Optional[float] = None
        self.duration_seconds: int = 0
        self.remaining_seconds: int = 0
        self.timer_thread: Optional[threading.Thread] = None
        self.session_type: str = ""
        self.task_description: str = ""
    
    def start(self, duration_minutes: int, session_type: str, task_description: str = ""):
        """Start a timer session"""
        if self.active:
            return False, "Timer is already running"
        
        self.duration_seconds = duration_minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.session_type = session_type
        self.task_description = task_description
        self.active = True
        self.paused = False
        self.start_time = time.time()
        
        # Start timer in separate thread
        self.timer_thread = threading.Thread(target=self._run_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        return True, f"Started {session_type} timer for {duration_minutes} minutes"
    
    def stop(self):
        """Stop the current timer"""
        if not self.active:
            return False, "No timer is running"
        
        self.active = False
        self.paused = False
        return True, "Timer stopped"
    
    def pause(self):
        """Pause the current timer"""
        if not self.active:
            return False, "No timer is running"
        
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        return True, f"Timer {status}"
    
    def get_status(self):
        """Get current timer status"""
        if not self.active:
            return {"active": False}
        
        return {
            "active": True,
            "paused": self.paused,
            "session_type": self.session_type,
            "task_description": self.task_description,
            "remaining_seconds": self.remaining_seconds,
            "remaining_minutes": self.remaining_seconds // 60,
            "remaining_display": self._format_time(self.remaining_seconds)
        }
    
    def _run_timer(self):
        """Run the timer countdown"""
        while self.active and self.remaining_seconds > 0:
            if not self.paused:
                self.remaining_seconds -= 1
            time.sleep(1)
        
        if self.active and self.remaining_seconds <= 0:
            # Timer completed
            self._on_timer_complete()
            self.active = False
    
    def _on_timer_complete(self):
        """Handle timer completion"""
        # Play notification sound
        if config.get("sound_enabled", True):
            self._play_notification_sound()
        
        # Show desktop notification
        if config.get("notifications_enabled", True):
            self._show_notification()
        
        print(f"\n🎉 {self.session_type.title()} session completed!")
    
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
            # Windows would use winsound, but we'll keep it simple for now
        except Exception:
            # If sound fails, just continue
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
            # If notification fails, just continue
            pass
    
    def _format_time(self, seconds: int) -> str:
        """Format time as MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

# Global timer instance
timer = Timer()
