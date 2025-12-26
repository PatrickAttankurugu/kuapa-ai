# Kuapa AI - Complete Usage Guide

This guide walks you through setting up and using Kuapa AI WhatsApp bot from start to finish.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting Your Gemini API Key](#getting-your-gemini-api-key)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Starting the Services](#starting-the-services)
6. [Authenticating WhatsApp](#authenticating-whatsapp)
7. [Using the Bot](#using-the-bot)
8. [Managing Services](#managing-services)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** - Check: `python3 --version`
- **Node.js 18+** - Check: `node --version`
- **npm** - Check: `npm --version`
- **Git** - Check: `git --version`
- **Active WhatsApp account** on your phone
- **Phone number** for the bot (default: +233551087418)

### Installing Prerequisites

**Ubuntu/Debian:**
```bash
# Python 3.10+
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11 node
```

---

## Getting Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select a Google Cloud project or create a new one
5. Click **"Create API key in existing project"**
6. Copy your API key (starts with `AIza...`)
7. Keep it safe - you'll need it in the next step!

**Note:** Gemini 2.0 Flash has a generous free tier:
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/kuapa-ai.git
cd kuapa-ai
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# Or on Windows:
# venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI (backend framework)
- Google Generative AI (Gemini)
- scikit-learn (RAG retrieval)
- pandas (data processing)
- pytest (testing)
- And other dependencies...

### Step 4: Install Node.js Dependencies

```bash
cd whatsapp-bot
npm install
cd ..
```

This will install:
- whatsapp-web.js (WhatsApp integration)
- qrcode-terminal (QR code display)
- axios (HTTP client)
- dotenv (environment management)

---

## Configuration

### Step 1: Configure Python Backend

```bash
# Copy environment template
cp .env.example .env

# Edit the .env file
nano .env  # or use your preferred editor
```

**Add your Gemini API key:**
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.35

DATABASE_URL=postgresql://user:password@localhost:5432/kuapa_ai

WHATSAPP_PHONE_NUMBER=+233551087418
PYTHON_API_URL=http://localhost:8000
```

**Important:**
- Replace `your_gemini_api_key_here` with your actual Gemini API key
- Keep `LLM_TEMPERATURE=0.35` for factual, agricultural advice
- Don't commit your `.env` file to Git!

### Step 2: Configure WhatsApp Bot

```bash
cd whatsapp-bot
cp .env.example .env
nano .env
```

**Default configuration (usually works as-is):**
```env
PYTHON_API_URL=http://localhost:8000
WHATSAPP_PHONE_NUMBER=+233551087418
SESSION_NAME=kuapa-ai-session
```

**Only change if:**
- Backend runs on different port: Update `PYTHON_API_URL`
- Different phone number: Update `WHATSAPP_PHONE_NUMBER`

---

## Starting the Services

### Option 1: Start Everything (Recommended)

```bash
# From the main kuapa-ai directory
./start-all.sh
```

This will:
1. Check and install dependencies if needed
2. Start Python backend on port 8000
3. Start WhatsApp bot
4. Display QR code for authentication
5. Save logs to `logs/` directory

**View logs:**
```bash
# WhatsApp bot logs (includes QR code)
tail -f logs/whatsapp.log

# Backend logs
tail -f logs/backend.log

# Both
tail -f logs/*.log
```

### Option 2: Start Services Separately

**Terminal 1 - Python Backend:**
```bash
./start-backend.sh

# Or manually:
# source venv/bin/activate
# python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - WhatsApp Bot:**
```bash
./start-whatsapp.sh

# Or manually:
# cd whatsapp-bot
# npm start
```

---

## Authenticating WhatsApp

### Step 1: Wait for QR Code

After starting the WhatsApp bot, you'll see:
```
🌾 Kuapa AI WhatsApp Bot - Starting...
🚀 Initializing WhatsApp client...

📱 Scan this QR code with your WhatsApp mobile app:

█████████████████████████████████
█████████████████████████████████
█████████████████████████████████
...

Waiting for authentication...
```

### Step 2: Scan with WhatsApp

1. Open **WhatsApp** on your phone
2. Tap the **three dots** menu (Android) or **Settings** (iPhone)
3. Select **"Linked Devices"**
4. Tap **"Link a Device"**
5. Point your phone camera at the **QR code** in the terminal
6. Wait for the scan to complete

### Step 3: Confirm Connection

You should see:
```
🔐 Authentication successful!
✅ Kuapa AI WhatsApp Bot is ready!
📞 Bot Phone Number: 233551087418
🔗 Connected to Python Backend: http://localhost:8000
🌾 Ready to help farmers with agricultural advice!
```

**Your bot is now live!** 🎉

---

## Using the Bot

### Sending Your First Message

From any WhatsApp account, send a message to your bot number: **+233551087418**

**Example 1: Start command**
```
You: hi

Bot: 🌾 *Welcome to Kuapa AI!*

I'm your agricultural advisor, here to help Ghanaian farmers with:
🌱 Crop management advice
🐛 Pest and disease control
🌧️ Irrigation and soil management
📅 Planting schedules
💡 Farming best practices

*How can I help you today?*

Example questions:
• How do I control fall armyworm?
• What are signs of nitrogen deficiency?
• When should I plant maize?
• How do I manage weeds?
```

### Asking Agricultural Questions

**Example 2: Pest control**
```
You: How do I control fall armyworm on my maize farm?

Bot: [Detailed advice from knowledge base + Gemini AI, including:
- Identification of fall armyworm
- Chemical control methods
- Biological control options
- Prevention strategies
- Source attribution]
```

**Example 3: Nutrient deficiency**
```
You: What are signs of nitrogen deficiency in maize?

Bot: [Comprehensive answer including:
- Visual symptoms (yellowing, stunted growth)
- Progression of symptoms
- Recommended fertilizers
- Application rates
- Timing
- Source: MoFA Ghana]
```

**Example 4: Planting advice**
```
You: When should I plant maize in Ghana?

Bot: [Seasonal planting schedule including:
- Major season (March-April)
- Minor season (September-October)
- Regional variations
- Rainfall considerations
- Source: Agricultural extension guidelines]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `/start` or `hi` | Welcome message and bot info |
| `/help` | Help information and usage examples |
| Any question | Get agricultural advice via RAG + Gemini |

### How the Bot Works

1. **You send a message** → WhatsApp
2. **Bot receives** → Node.js WhatsApp service
3. **Forwards to backend** → Python FastAPI
4. **RAG Retrieval** → Searches 61+ agricultural Q&As using TF-IDF
5. **Gemini AI** → Generates response based on context
6. **Bot replies** → WhatsApp message to you

**Response time:** Typically 2-5 seconds

---

## Managing Services

### Checking Service Status

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check running processes
ps aux | grep -E "uvicorn|node bot"

# Check logs
tail -f logs/*.log
```

### Stopping Services

```bash
# Stop all services
./stop-all.sh

# Or manually
pkill -f "uvicorn"
pkill -f "node bot.js"
```

### Restarting Services

```bash
# After making changes to code or configuration
./stop-all.sh
./start-all.sh
```

### Viewing Logs

```bash
# Real-time WhatsApp bot logs
tail -f logs/whatsapp.log

# Real-time backend logs
tail -f logs/backend.log

# View last 50 lines
tail -n 50 logs/whatsapp.log

# Search logs
grep "error" logs/*.log
```

---

## Troubleshooting

### QR Code Not Appearing

**Problem:** Terminal shows "Starting..." but no QR code

**Solution:**
```bash
# Check if bot is actually running
ps aux | grep "node bot"

# View logs
tail -f logs/whatsapp.log

# Restart
./stop-all.sh
./start-whatsapp.sh
```

### Authentication Fails

**Problem:** QR code scan fails or expires

**Solution:**
```bash
# Delete session and restart
rm -rf whatsapp-bot/.wwebjs_auth/
./start-whatsapp.sh
```

### Bot Not Responding

**Problem:** Messages sent but no response

**Solutions:**

1. **Check backend is running:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

2. **Check Gemini API key:**
```bash
cat .env | grep GEMINI_API_KEY
# Should show your API key
```

3. **View error logs:**
```bash
tail -f logs/backend.log
tail -f logs/whatsapp.log
```

4. **Test backend directly:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I plant maize?"}'
```

### "Sorry, I'm currently not configured" Error

**Problem:** Bot responds with configuration error

**Cause:** Gemini API key is missing or invalid

**Solution:**
```bash
# Check if GEMINI_API_KEY is set
cat .env | grep GEMINI_API_KEY

# If missing or invalid, edit .env
nano .env

# Add valid API key
GEMINI_API_KEY=AIzaSy...your_key_here

# Restart backend
./stop-all.sh
./start-backend.sh
```

### Port 8000 Already in Use

**Problem:** Backend won't start because port is in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
# Update PYTHON_API_URL in whatsapp-bot/.env accordingly
```

### WhatsApp Disconnects

**Problem:** Bot disconnects after some time

**Solution:**
- This is normal behavior for WhatsApp Web
- The bot will automatically attempt to reconnect
- Check logs: `tail -f logs/whatsapp.log`
- If it doesn't reconnect, restart: `./start-whatsapp.sh`

---

## Advanced Configuration

### Customizing the Agricultural Knowledge Base

The bot's knowledge comes from `data/agriculture_qna_expanded.csv`. To add more Q&As:

1. **Edit the CSV file:**
```bash
nano data/agriculture_qna_expanded.csv
```

2. **Add rows in format:**
```csv
"Question","Answer","Source"
"How do I control aphids?","Use neem oil spray or introduce ladybugs as biological control. Apply neem oil solution (5ml/L water) weekly.","MoFA Ghana"
```

3. **Restart backend to reload data:**
```bash
./stop-all.sh
./start-all.sh
```

### Adjusting AI Response Style

Edit `.env` to change Gemini's behavior:

```env
# More creative/varied responses (0.0 - 1.0)
LLM_TEMPERATURE=0.7

# More factual/consistent responses (default)
LLM_TEMPERATURE=0.35

# Very strict, minimal variation
LLM_TEMPERATURE=0.1
```

### Using a Different Phone Number

1. **Edit `.env` files:**
```bash
nano .env
# Change: WHATSAPP_PHONE_NUMBER=+233123456789

nano whatsapp-bot/.env
# Change: WHATSAPP_PHONE_NUMBER=+233123456789
```

2. **Delete old session:**
```bash
rm -rf whatsapp-bot/.wwebjs_auth/
```

3. **Restart and re-authenticate:**
```bash
./start-all.sh
# Scan QR code with the new phone number
```

### Enabling Debug Mode

For more detailed logging:

**Backend:**
```bash
# In start-backend.sh or manually
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

**WhatsApp Bot:**
```javascript
// In whatsapp-bot/bot.js, add:
console.log('Debug:', JSON.stringify(message, null, 2));
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_health_endpoint -v
```

---

## Production Deployment

For production deployment, see the main [README.md](README.md) sections on:
- PM2 process management
- Systemd services
- Cloud platform deployment

---

## Getting Help

1. **Check logs first:** `tail -f logs/*.log`
2. **Test services:**
   - Backend: `curl http://localhost:8000/health`
   - WhatsApp: Check for QR code in logs
3. **Review environment:** Check `.env` files for correct configuration
4. **GitHub Issues:** [Report bugs or ask questions](https://github.com/yourusername/kuapa-ai/issues)
5. **Documentation:** Read [README.md](README.md) and [whatsapp-bot/README.md](whatsapp-bot/README.md)

---

## Next Steps

Now that your bot is running:

1. **Test with farmers:** Share your bot number with farmers for real-world testing
2. **Monitor logs:** Keep an eye on `logs/` for errors or issues
3. **Expand knowledge base:** Add more Q&As to `data/agriculture_qna_expanded.csv`
4. **Customize responses:** Adjust temperature and system prompts
5. **Deploy to production:** Use PM2 or systemd for always-on operation
6. **Contribute:** Share improvements back to the project!

---

**Happy farming! 🌾**

For questions or issues, contact: [GitHub Issues](https://github.com/yourusername/kuapa-ai/issues)
