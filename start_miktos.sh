#!/bin/bash

# Miktos AI Bridge Platform Launcher
cd /Users/atorrella/Desktop/Miktos/development/miktos-workflows

# Set environment variables
export PYTHONPATH="/Users/atorrella/Desktop/Miktos/development/miktos-workflows:/Users/atorrella/Desktop/Miktos/development/miktos-workflows/miktos_env/lib/python3.13/site-packages"

# Use the virtual environment Python
/opt/homebrew/opt/python@3.13/bin/python3.13 main.py --interactive
