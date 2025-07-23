#!/bin/bash

# Miktos AI Bridge Platform Launch Script

# Navigate to the correct directory
cd /Users/atorrella/Desktop/Miktos/development/miktos-workflows

# Set up the Python environment
export PYTHONPATH="/Users/atorrella/Desktop/Miktos/development/miktos-workflows/miktos_env/lib/python3.13/site-packages:$PYTHONPATH"

# Launch Miktos in interactive mode
echo "🚀 Starting Miktos AI Bridge Platform..."
echo "📂 Working Directory: $(pwd)"
echo "🐍 Python Path: $PYTHONPATH"
echo "⚡ Launching Interactive Mode..."
echo ""

python3 main.py --interactive
