#!/bin/bash

# Kuapa AI - Stop All Services
# This script stops both the Python backend and WhatsApp bot

echo "🛑 Stopping Kuapa AI Services..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Stop backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${RED}Stopping Python Backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm logs/backend.pid
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend already stopped"
        rm logs/backend.pid
    fi
else
    echo "⚠️  No backend PID file found"
fi

# Stop WhatsApp bot
if [ -f logs/whatsapp.pid ]; then
    BOT_PID=$(cat logs/whatsapp.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${RED}Stopping WhatsApp Bot (PID: $BOT_PID)...${NC}"
        kill $BOT_PID
        rm logs/whatsapp.pid
        echo "✅ WhatsApp Bot stopped"
    else
        echo "⚠️  WhatsApp Bot already stopped"
        rm logs/whatsapp.pid
    fi
else
    echo "⚠️  No WhatsApp bot PID file found"
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
