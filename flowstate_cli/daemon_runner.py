#!/usr/bin/env python3
"""
Daemon runner script for FlowState timer.
This script runs the timer daemon process in the background.
"""

import os
import sys
import time
import signal
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from daemon import TimerDaemon

def main():
    """Main daemon process"""
    daemon = TimerDaemon()
    
    # Save PID
    with open(daemon.pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        daemon._clear_state()
        if daemon.pid_file.exists():
            daemon.pid_file.unlink()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Main daemon loop
    try:
        while True:
            # Load current state
            daemon._load_state()
            
            if daemon.active and not daemon.paused:
                daemon.remaining_seconds -= 1
                if daemon.remaining_seconds <= 0:
                    daemon._on_timer_complete()
                    daemon.active = False
                
                daemon._save_state()
            
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
