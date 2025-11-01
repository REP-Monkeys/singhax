#!/bin/bash

# Restart Backend Server Script
# This script properly restarts the backend with environment variables loaded

echo "=================================================="
echo "🔄 RESTARTING BACKEND SERVER"
echo "=================================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/apps/backend" || exit 1

# Check if .env file exists in project root
if [ -f "../../.env" ]; then
    echo "✅ Found .env file"
else
    echo "❌ No .env file found at project root!"
    echo "   Please create one from infra/env.example"
    exit 1
fi

# Stop any existing backend process on port 8000
echo ""
echo "🛑 Stopping any existing backend on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "   No existing process found"

echo ""
echo "🚀 Starting backend server..."
echo ""
echo "Server will be available at:"
echo "  - http://localhost:8000"
echo "  - http://localhost:8000/docs (API documentation)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=================================================="
echo ""

# Start the server
# The .env will be loaded by the updated config.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

