#!/bin/bash

# Start only the WhatsApp bot

echo "📱 Starting Kuapa AI WhatsApp Bot..."

# Check if .env exists
if [ ! -f whatsapp-bot/.env ]; then
    echo "⚠️  Error: whatsapp-bot/.env file not found"
    echo "Please copy whatsapp-bot/.env.example to whatsapp-bot/.env and configure it"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Python backend doesn't seem to be running on port 8000"
    echo "Please start the backend first with: ./start-backend.sh"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start WhatsApp bot
cd whatsapp-bot
npm start
