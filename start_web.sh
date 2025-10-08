#!/bin/bash

# ====================================================================
# Start Script - Terminal 3: Flask Web UI
# ====================================================================

PROJECT_DIR="/home/david/Downloads/Apache_Flume_Demo"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "Starting Flask Web UI"
echo "======================================================================"

# Activate virtual environment
source venv/bin/activate

# Run Flask app
python web_ui/app.py
