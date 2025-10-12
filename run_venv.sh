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
    echo "🚀 Starting News Reader Application..."
    python news_reader/main.py
else
    if [ "$1" = "app" ] || [ "$1" = "start" ]; then
        echo "🚀 Starting News Reader Application..."
        python news_reader/main.py
    else
        echo "❌ Unknown command: $1"
        echo "Available commands:"
        echo "  app/start (or no arguments) - Start the unified News Reader application"
        echo ""
        echo "Usage: $0 [app|start]"
        echo "Example: $0 app"
        exit 1
    fi
fi
