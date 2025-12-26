#!/bin/bash

# Start only the Python backend

echo "🐍 Starting Kuapa AI Python Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Start backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
