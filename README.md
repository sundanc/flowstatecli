# FlowState CLI - Lightweight Hybrid Productivity Tool

A minimal command-line interface for task management and Pomodoro timers that works both online and offline.

## ✨ Features

- **🔄 Hybrid Mode**: Seamlessly switch between cloud sync and offline-first operation
- **📝 Task Management**: Create, track, and complete tasks with local SQLite storage
- **🍅 Pomodoro Timer**: Built-in timer with background daemon support
- **⚡ Offline-First**: Full functionality without internet connection
- **🔒 Local Authentication**: No cloud dependency for basic features
- **📊 Simple Sync**: Manual sync when you want it
- **💾 Lightweight**: Minimal dependencies, SQLite database

## 🚀 Quick Installation

```bash
# Clone and install
git clone <repository-url>
cd flowstatecli
chmod +x install.sh
./install.sh
```

Or install manually:
```bash
pip install -r requirements.txt
pip install -e .
```

## 🎯 Operating Modes

FlowState CLI supports three lightweight operating modes:

### 1. Hybrid Mode (Default)
- Prefers cloud sync when online
- Falls back to local storage when offline
- Best of both worlds

### 2. Local Mode
- Completely offline operation
- Local SQLite database
- Zero external dependencies

### 3. Cloud Mode
- Uses cloud API when available
- Requires internet connection
- Traditional online experience

## ⚙️ Configuration

### Quick Setup
```bash
# Set operating mode
flowstate mode set hybrid  # or 'local' or 'cloud'

# Check current status
flowstate mode status

# For local/hybrid modes, create local account (username-based)
flowstate auth local-register

# For cloud mode, use magic link (email-based)
flowstate auth login your-email@example.com
```

### Mode Management
```bash
# Switch modes anytime
flowstate mode set local     # Go offline-only
flowstate mode set cloud     # Go cloud-only  
flowstate mode set hybrid    # Best of both

# Manual sync (hybrid/cloud modes)
flowstate sync now

# Check connectivity and auth status
flowstate mode status
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

## 🔄 Data Synchronization

### Manual Sync
```bash
# Force sync now (hybrid/cloud modes)
flowstate sync now

# Check sync status
flowstate mode status
```

### Conflict Resolution
- **Simple approach**: Local changes take priority
- **Manual sync**: Sync only when you want it
- **Lightweight**: No complex background processes

## 💾 Local Storage

All data is stored locally in `~/.flowstate/`:
- `config.json` - User preferences and mode settings
- `local.db` - SQLite database with tasks and pomodoros
- `auth.json` - Local authentication tokens

## 📊 Dependencies

Minimal and lightweight:
- **Core**: `typer`, `rich`, `httpx` (for cloud features)
- **Database**: `sqlalchemy` (with SQLite)  
- **Auth**: `bcrypt`, `PyJWT` (for local auth)
- **Notifications**: `plyer` (optional system notifications)

Total install size: ~15MB

## 📊 Authentication Options

### Local Authentication
```bash
# Register new local account (username-based)
flowstate auth local-register

# Login to existing local account  
flowstate auth local-login

# Logout from current session
flowstate auth logout
```

### Cloud Authentication  
```bash
# Magic link authentication (email-based)
flowstate auth login your-email@example.com
flowstate auth token <your-cli-token>

# Check auth status
flowstate mode status
```
