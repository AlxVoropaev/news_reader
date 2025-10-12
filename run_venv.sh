#!/bin/bash

# Helper script to run News Reader commands in virtual environment

ENV_DIR=".venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/$ENV_DIR" ]; then
    echo "❌ Virtual environment '$ENV_DIR' not found."
    echo "Creating virtual environment..."
    cd "$SCRIPT_DIR"
    python3 -m venv "$ENV_DIR"
    echo "✅ Virtual environment created."
    echo "Installing requirements..."
    source "$ENV_DIR/bin/activate"
    pip install -r requirements.txt
    echo "✅ Requirements installed."
else
    echo "🐍 Activating virtual environment '$ENV_DIR'..."
    source "$SCRIPT_DIR/$ENV_DIR/bin/activate"
fi

if [ $# -eq 0 ]; then
    echo "📋 Available commands:"
    echo "  connect                    - Connect and authorize"
    echo "  monitor                    - Start monitoring service"
    echo ""
    echo "Usage: $0 <command> [arguments]"
    echo "Example: $0 connect"
else
    if [ "$1" = "monitor" ]; then
        echo "🔍 Starting monitoring service..."
        python news_reader/monitor.py
    elif [ "$1" = "connect" ]; then
        echo "🚀 Running: python news_reader/commander.py connect"
        python news_reader/commander.py connect
    else
        echo "❌ Unknown command: $1"
        echo "Available commands: connect, monitor"
        exit 1
    fi
fi
