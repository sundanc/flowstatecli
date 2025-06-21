# FlowState CLI Client

A command-line interface for the FlowState productivity tool.

## Installation

```bash
pip install -e .
```

## Configuration

First, authenticate with the FlowState service:

```bash
flowstate auth login your-email@example.com
```

Check your email for the magic link and follow the instructions.

To complete authentication with your token:
```bash
flowstate auth token <your-token>
```

## Usage

### Task Management
```bash
# Add a new task
flowstate add "Fix the authentication bug"

# List all tasks
flowstate list

# Start working on a task
flowstate start 1

# Complete a task
flowstate done 1

# Delete a task
flowstate rm 1
```

### Pomodoro Timer
```bash
# Start a 25-minute focus session
flowstate pom start

# Take a short break (5 minutes)
flowstate pom break short

# Take a long break (15 minutes)
flowstate pom break long

# Stop current timer
flowstate pom stop

# Show current timer status
flowstate pom status
```

### Flow State Mode
```bash
# Block distracting websites
flowstate mode on

# Unblock websites
flowstate mode off

# Show flow state mode status
flowstate mode status
```

### Productivity Stats
```bash
# Show your productivity statistics
flowstate stats
```

### Configuration
```bash
# Show current settings
flowstate config show

# Update Pomodoro duration to 30 minutes
flowstate config set pomo_duration 30

# Update short break duration to 10 minutes
flowstate config set short_break 10

# Update long break duration to 20 minutes
flowstate config set long_break 20

# Enable notifications
flowstate config set notifications true

# Disable notifications
flowstate config set notifications false
```
