#!/bin/bash

# ====================================================================
# Start Script - Terminal 1: Reddit Streamer
# ====================================================================

PROJECT_DIR="/home/david/Downloads/Apache_Flume_Demo"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "Starting Reddit Streamer"
echo "======================================================================"

# Activate virtual environment
source venv/bin/activate

# Run Reddit client
python reddit_streamer/reddit_client.py
