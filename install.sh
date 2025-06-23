#!/bin/bash

# FlowState CLI Lightweight Installation Script
set -e

echo "🚀 Installing FlowState CLI with hybrid offline/online support..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Install dependencies
echo "📦 Installing lightweight dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Install FlowState CLI
echo "🔧 Installing FlowState CLI..."
pip3 install -e .

# Create config directory
echo "📁 Setting up configuration..."
mkdir -p ~/.flowstate

# Set default mode to hybrid
echo "⚙️ Configuring hybrid mode..."
flowstate mode set hybrid

echo ""
echo "✅ FlowState CLI installation complete!"
echo ""
echo "🎯 Quick Start:"
echo "  • flowstate mode status               # Check current mode"
echo "  • flowstate auth local-register       # Create local account (username + password)"
echo "  • flowstate add \"My first task\"       # Add a task"
echo "  • flowstate list                      # List tasks"
echo "  • flowstate pom start                # Start pomodoro timer"
echo ""
echo "🔄 Mode Management:"
echo "  • flowstate mode set local            # Local-only mode (username-based)"
echo "  • flowstate mode set cloud            # Cloud-only mode (email-based)" 
echo "  • flowstate mode set hybrid           # Hybrid mode (default)"
echo "  • flowstate sync now                  # Manual sync"
echo ""
echo "💾 Local Storage:"
echo "  • All data stored in ~/.flowstate/"
echo "  • Lightweight SQLite database"
echo "  • No external dependencies"
echo "  • Username-based for privacy"
echo ""
echo "📚 For more help: flowstate --help"
