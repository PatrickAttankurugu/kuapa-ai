#!/bin/bash

# Kuapa AI - Start All Services
# This script starts both the Python backend and WhatsApp bot

set -e

echo "🌾 Kuapa AI - Starting All Services"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found in root directory${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and add your GEMINI_API_KEY${NC}"
    echo ""
fi

# Check if whatsapp-bot/.env exists
if [ ! -f whatsapp-bot/.env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found in whatsapp-bot directory${NC}"
    echo "Creating whatsapp-bot/.env from .env.example..."
    cp whatsapp-bot/.env.example whatsapp-bot/.env
    echo ""
fi

# Check Python dependencies
echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
if ! pip show google-generativeai > /dev/null 2>&1; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Python dependencies already installed"
fi
echo ""

# Check Node.js dependencies
echo -e "${BLUE}📦 Checking Node.js dependencies...${NC}"
cd whatsapp-bot
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies already installed"
fi
cd ..
echo ""

# Create logs directory
mkdir -p logs

# Start Python Backend
echo -e "${GREEN}🐍 Starting Python Backend (Port 8000)...${NC}"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
echo $BACKEND_PID > logs/backend.pid

# Wait for backend to start
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Backend might not be ready yet, but continuing...${NC}"
    fi
    sleep 1
done
echo ""

# Start WhatsApp Bot
echo -e "${GREEN}📱 Starting WhatsApp Bot...${NC}"
cd whatsapp-bot
node bot.js > ../logs/whatsapp.log 2>&1 &
BOT_PID=$!
echo "WhatsApp Bot PID: $BOT_PID"
echo $BOT_PID > ../logs/whatsapp.pid
cd ..
echo ""

echo -e "${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "📊 Service Status:"
echo "  • Python Backend: http://localhost:8000"
echo "  • WhatsApp Bot: Running (check logs/whatsapp.log for QR code)"
echo ""
echo "📝 Log Files:"
echo "  • Backend: logs/backend.log"
echo "  • WhatsApp: logs/whatsapp.log"
echo ""
echo "⚠️  To view WhatsApp QR code, run: tail -f logs/whatsapp.log"
echo ""
echo "🛑 To stop all services, run: ./stop-all.sh"
echo ""
