#!/bin/bash

# Helper script to run News Reader commands in virtual environment

ENV_NAME="news-reader"

# Check if virtualenvwrapper is available
if ! command -v workon &> /dev/null; then
    echo "❌ virtualenvwrapper not found. Please install it first."
    echo "Run: pip3 install virtualenvwrapper"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$WORKON_HOME/$ENV_NAME" ]; then
    echo "❌ Virtual environment '$ENV_NAME' not found."
    echo "Please run ./setup.sh and choose option 2 to create it."
    exit 1
fi

# Activate virtual environment and run the command
echo "🐍 Activating virtual environment '$ENV_NAME'..."
source "$WORKON_HOME/$ENV_NAME/bin/activate"

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
