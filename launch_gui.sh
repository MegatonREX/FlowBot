#!/bin/bash
# FlowBot GUI Launcher for Linux/macOS
# This script launches the FlowBot GUI application

echo ""
echo "========================================"
echo "  FlowBot - AI Workflow Assistant"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if PyQt6 is installed
if ! python3 -c "import PyQt6" &> /dev/null; then
    echo "WARNING: PyQt6 is not installed"
    echo "Installing required dependencies..."
    echo ""
    pip3 install -r requirements_gui.txt
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo "Starting FlowBot GUI..."
echo ""
python3 gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: FlowBot GUI encountered an error"
fi
