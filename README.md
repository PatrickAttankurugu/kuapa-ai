# Kuapa AI - Agricultural Advisory WhatsApp Assistant

A WhatsApp-based AI agricultural advisory system that helps Ghanaian farmers get instant, reliable advice about farming, crops, pests, and diseases directly through WhatsApp.

## Overview

Kuapa AI addresses Ghana's 1:1500 ratio of extension officers to farmers, providing millions of farmers with timely support through an intelligent question-answering system accessible via WhatsApp - the most popular messaging platform in Ghana.

This system features:
- **WhatsApp Integration**: Chat directly via WhatsApp Web
- **RAG-Powered**: Retrieval-augmented generation for accurate agricultural advice
- **Google Gemini 2.5 Flash**: Fast, efficient AI responses
- **Open Source**: All tools are open source except the LLM
- **Real-time Processing**: Instant responses to farmer questions
- **Clean, Production-Ready**: Well-tested, documented codebase

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **WhatsApp Interface** | whatsapp-web.js (Node.js) |
| **Backend** | FastAPI, Python 3.10+ |
| **LLM** | Google Gemini 2.5 Flash |
| **RAG Retrieval** | scikit-learn (TF-IDF vectorization) |
| **Real-time** | WebSockets |
| **Database** | PostgreSQL + pgvector (ready) |
| **Testing** | pytest, pytest-asyncio |
| **Speech** | gTTS (Text-to-Speech, optional) |

## Architecture

```
WhatsApp User (Farmer)
    ↓
WhatsApp Cloud
    ↓
WhatsApp Web.js Client (Node.js)
    ↓ HTTP POST /chat
Python FastAPI Backend
    ↓
RAG Retrieval System
    ├── TF-IDF Vectorization
    ├── Cosine Similarity Search
    └── Context Retrieval (Top 8 chunks)
    ↓
Google Gemini 2.5 Flash
    ├── System Prompt (Agricultural Advisor)
    ├── User Query
    └── Retrieved Context
    ↓
AI-Generated Response
    ↓
WhatsApp Web.js Client
    ↓
WhatsApp User (Farmer)
```

### System Components

1. **WhatsApp Bot Layer** (Node.js)
   - Handles WhatsApp Web authentication via QR code
   - Receives and sends messages
   - Maintains conversation sessions
   - Error handling and retry logic

2. **Python Backend** (FastAPI)
   - REST API endpoints for chat processing
   - RAG retrieval system with TF-IDF
   - Integration with Google Gemini
   - Structured logging and monitoring

3. **Knowledge Base**
   - 61+ agricultural Q&A pairs
   - Sources: MoFA Ghana, CSIR-CRI, Yara Ghana
   - CSV-based (expandable to vector DB)

4. **LLM** (Google Gemini 2.5 Flash)
   - Fast, efficient responses
   - Temperature: 0.35 (factual, low hallucination)
   - Max tokens: 256 (concise answers)

## Project Structure

```
kuapa-ai/
├── api/                          # Python Backend (FastAPI)
│   ├── main.py                  # FastAPI app with REST & WebSocket
│   ├── config.py                # Environment configuration
│   ├── logger.py                # Structured JSON logging
│   ├── rag.py                   # RAG orchestration
│   ├── llm.py                   # Gemini LLM integration
│   ├── tts_en_google.py         # Text-to-speech (gTTS)
│   └── utils_fallback_retriever.py  # TF-IDF retriever
│
├── whatsapp-bot/                 # Node.js WhatsApp Service
│   ├── bot.js                   # Main WhatsApp bot
│   ├── package.json             # Node.js dependencies
│   ├── .env.example             # WhatsApp config template
│   └── README.md                # WhatsApp bot documentation
│
├── data/                         # Agricultural Knowledge Base
│   └── agriculture_qna_expanded.csv  # 61 Q&A pairs
│
├── tests/                        # Test Suite
│   ├── test_api.py              # API endpoint tests
│   ├── test_retriever.py        # Retriever tests
│   └── test_rag.py              # RAG integration tests
│
├── db/                           # Database (PostgreSQL + pgvector)
│   └── migrations.sql           # Schema definitions
│
├── static/                       # Legacy Web Interface
│   ├── index.html               # (Optional - for testing)
│   ├── styles.css
│   └── app.js
│
├── start-all.sh                  # Start both services
├── start-backend.sh              # Start Python backend only
├── start-whatsapp.sh             # Start WhatsApp bot only
├── stop-all.sh                   # Stop all services
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Installation

### Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** installed
- **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))
- **Phone number** for WhatsApp bot (+233551087418 configured by default)
- **Active WhatsApp account** on your phone

### Quick Start (Automated)

The fastest way to get started:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/kuapa-ai.git
cd kuapa-ai

# 2. Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start all services (installs dependencies automatically)
./start-all.sh

# 4. Scan the QR code that appears with WhatsApp on your phone
# 5. Start chatting with your bot!
```

### Manual Setup (Step by Step)

#### Step 1: Clone and Setup Python Backend

```bash
# Clone repository
git clone https://github.com/yourusername/kuapa-ai.git
cd kuapa-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your GEMINI_API_KEY
```

**Required in `.env`:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.35
```

#### Step 2: Setup WhatsApp Bot

```bash
# Navigate to WhatsApp bot directory
cd whatsapp-bot

# Install Node.js dependencies
npm install

# Configure WhatsApp environment
cp .env.example .env
nano .env  # Adjust settings if needed
```

**WhatsApp `.env` configuration:**
```env
PYTHON_API_URL=http://localhost:8000
WHATSAPP_PHONE_NUMBER=+233551087418
SESSION_NAME=kuapa-ai-session
```

#### Step 3: Start Services

**Option A: Start everything together**
```bash
cd ..
./start-all.sh
```

**Option B: Start services separately**

Terminal 1 - Python Backend:
```bash
./start-backend.sh
# Or manually:
# python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - WhatsApp Bot:
```bash
./start-whatsapp.sh
# Or manually:
# cd whatsapp-bot && npm start
```

#### Step 4: Authenticate WhatsApp

1. When the bot starts, a **QR code** will appear in the terminal
2. Open **WhatsApp** on your phone
3. Go to **Settings → Linked Devices**
4. Tap **"Link a Device"**
5. **Scan the QR code** from your terminal
6. Wait for "✅ Kuapa AI WhatsApp Bot is ready!" message

#### Step 5: Test the Bot

Send a message to your bot number (+233551087418):

```
Hi
```

You should receive a welcome message! Try asking:
```
How do I control fall armyworm?
```

## API Documentation

### REST Endpoints

#### GET /
Health check endpoint
```bash
curl http://localhost:8000/
```

#### GET /health
Detailed health status
```bash
curl http://localhost:8000/health
```

#### POST /chat
Text-based chat endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are symptoms of nitrogen deficiency in maize?"}'
```

Response:
```json
{
  "response": "Nitrogen-starved maize grows slowly...",
  "request_id": "uuid-here",
  "timings_ms": {
    "rag": 150,
    "llm": 3200,
    "total": 3350
  }
}
```

#### POST /process_audio
Audio processing endpoint (WAV files)
```bash
curl -X POST http://localhost:8000/process_audio \
  -F "file=@audio.wav"
```

### WebSocket Endpoint

#### WS /ws/{client_id}
Real-time chat via WebSocket

Connect:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.response);
};

ws.send('What crops grow well in Ghana?');
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=api --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_api.py -v
```

## Configuration

### Python Backend Environment Variables

**Main `.env` file:**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | - | ✅ Yes |
| `GEMINI_MODEL` | Gemini model name | gemini-2.0-flash-exp | No |
| `LLM_TEMPERATURE` | Response creativity (0-1) | 0.35 | No |
| `DATABASE_URL` | PostgreSQL connection | - | No (future) |
| `WHATSAPP_PHONE_NUMBER` | Bot phone number | +233551087418 | No |
| `PYTHON_API_URL` | Backend URL | http://localhost:8000 | No |

### WhatsApp Bot Environment Variables

**WhatsApp `.env` file:**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PYTHON_API_URL` | Python backend URL | http://localhost:8000 | Yes |
| `WHATSAPP_PHONE_NUMBER` | Bot's phone number | +233551087418 | No |
| `SESSION_NAME` | WhatsApp session ID | kuapa-ai-session | No |

## Features

### Current Features

**WhatsApp Integration:**
- ✅ Full WhatsApp Web.js integration
- ✅ QR code authentication
- ✅ Automatic session persistence
- ✅ Real-time message handling
- ✅ Typing indicators
- ✅ Error messages to users
- ✅ Special commands (`/start`, `/help`)
- ✅ Conversation context tracking

**AI & RAG:**
- ✅ Google Gemini 2.5 Flash LLM
- ✅ RAG-based question answering with TF-IDF
- ✅ 61+ agricultural Q&A knowledge base
- ✅ Source attribution for answers
- ✅ Temperature-controlled responses (factual)
- ✅ Context-aware retrieval (Top 8 chunks)

**Backend:**
- ✅ FastAPI REST endpoints
- ✅ WebSocket support (for future web UI)
- ✅ Structured JSON logging with request tracking
- ✅ Comprehensive error handling
- ✅ Health check endpoints
- ✅ Type hints throughout codebase
- ✅ Comprehensive test coverage (pytest)

**Infrastructure:**
- ✅ Easy start/stop scripts
- ✅ Process management ready (PM2, systemd)
- ✅ Environment-based configuration
- ✅ Production-ready architecture

### WhatsApp Bot Commands

| Command | Description |
|---------|-------------|
| `/start` or `hi` | Welcome message with bot info |
| `/help` | Help information and usage examples |
| Any question | Agricultural advice via RAG + Gemini |

### Example Interactions

**User:** "Hi"
**Bot:** 🌾 Welcome message with instructions

**User:** "How do I control fall armyworm?"
**Bot:** [Detailed advice from knowledge base + Gemini]

**User:** "What are signs of nitrogen deficiency?"
**Bot:** [Symptoms, causes, and solutions from agricultural sources]

**User:** "When should I plant maize in Ghana?"
**Bot:** [Planting schedule advice based on Ghanaian agricultural calendar]

### Planned Features

- 🔄 Twi language support (local language)
- 🔄 Voice message support (speech-to-text)
- 🔄 Image recognition for crop disease diagnosis
- 🔄 Semantic search with pgVector
- 🔄 User profiles and conversation history
- 🔄 Enhanced agricultural dataset (1000+ Q&As)
- 🔄 Weather integration
- 🔄 Market price information
- 🔄 Multi-user session management
- 🔄 Analytics dashboard

## Development

### Code Quality

The codebase follows these standards:
- Type hints on all functions
- Comprehensive logging with request tracking
- Error handling with proper HTTP status codes
- Async/await for I/O operations
- Clean separation of concerns

### Adding New Agricultural Knowledge

1. Edit `data/agriculture_qna_expanded.csv`
2. Add rows with: question, answer, source
3. Restart the server to reload the dataset

Example:
```csv
"How do I control aphids?","Use neem oil spray or introduce ladybugs","MoFA Ghana"
```

## Managing Services

### Starting Services

```bash
# Start all services (backend + WhatsApp bot)
./start-all.sh

# Start only Python backend
./start-backend.sh

# Start only WhatsApp bot
./start-whatsapp.sh
```

### Stopping Services

```bash
# Stop all services
./stop-all.sh

# Or manually kill processes
pkill -f "uvicorn"
pkill -f "node bot.js"
```

### Monitoring

**Check logs:**
```bash
# Backend logs
tail -f logs/backend.log

# WhatsApp bot logs (includes QR code)
tail -f logs/whatsapp.log

# Both logs
tail -f logs/*.log
```

**Check service status:**
```bash
# Backend health
curl http://localhost:8000/health

# Process status
ps aux | grep -E "uvicorn|node bot"
```

### Restarting After Changes

```bash
# Stop services
./stop-all.sh

# Make your changes...

# Start again
./start-all.sh
```

## Deployment

### Production Deployment with PM2 (Recommended)

**Install PM2:**
```bash
npm install -g pm2
```

**Create PM2 ecosystem file:**
```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'kuapa-backend',
      script: 'python',
      args: '-m uvicorn api.main:app --host 0.0.0.0 --port 8000',
      cwd: '/path/to/kuapa-ai',
      interpreter: '/path/to/venv/bin/python',
      env: {
        GEMINI_API_KEY: 'your_key_here'
      }
    },
    {
      name: 'kuapa-whatsapp',
      script: 'bot.js',
      cwd: '/path/to/kuapa-ai/whatsapp-bot',
      interpreter: 'node'
    }
  ]
};
```

**Start with PM2:**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable auto-start on boot
```

**Manage with PM2:**
```bash
pm2 status          # Check status
pm2 logs            # View logs
pm2 restart all     # Restart all
pm2 stop all        # Stop all
pm2 monit           # Live monitoring
```

### Systemd Service (Linux)

**Create backend service:**
```ini
# /etc/systemd/system/kuapa-backend.service
[Unit]
Description=Kuapa AI Backend
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/kuapa-ai
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Create WhatsApp service:**
```ini
# /etc/systemd/system/kuapa-whatsapp.service
[Unit]
Description=Kuapa AI WhatsApp Bot
After=network.target kuapa-backend.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/kuapa-ai/whatsapp-bot
ExecStart=/usr/bin/node bot.js
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable kuapa-backend kuapa-whatsapp
sudo systemctl start kuapa-backend kuapa-whatsapp
sudo systemctl status kuapa-backend kuapa-whatsapp
```

### Cloud Platforms

**Python Backend** can be deployed on:
- Render
- Railway
- Heroku
- AWS EC2/ECS
- Google Cloud Run
- DigitalOcean App Platform

**WhatsApp Bot** needs persistent storage for `.wwebjs_auth/`:
- VPS (DigitalOcean, Linode, AWS EC2)
- Heroku with persistent volumes
- Any server with file system access

**Important:** WhatsApp Web.js requires a persistent file system for authentication. Serverless platforms (Lambda, Cloud Functions) won't work for the WhatsApp bot.

## Troubleshooting

### WhatsApp Bot Issues

#### QR Code Not Showing
```bash
# Check if bot is running
ps aux | grep "node bot"

# View bot logs
tail -f logs/whatsapp.log

# Restart the bot
./stop-all.sh && ./start-all.sh
```

#### Authentication Fails
```bash
# Delete session and try again
rm -rf whatsapp-bot/.wwebjs_auth/
./start-whatsapp.sh
```

#### Bot Not Responding to Messages
```bash
# Check backend is running
curl http://localhost:8000/health

# Check bot logs
tail -f logs/whatsapp.log

# Check backend logs
tail -f logs/backend.log

# Verify environment variables
cat .env | grep GEMINI_API_KEY
```

#### "Sorry, I'm currently not configured" Error
This means the Gemini API key is missing or invalid:
```bash
# Check if GEMINI_API_KEY is set
cat .env | grep GEMINI_API_KEY

# Test API key manually
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Backend Issues

#### Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

#### Python Dependencies Missing
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Node.js Dependencies Missing
```bash
cd whatsapp-bot
rm -rf node_modules package-lock.json
npm install
```

### Common Errors

#### Error: "ECONNREFUSED"
Backend is not running. Start it:
```bash
./start-backend.sh
```

#### Error: "401 Unauthorized" (Gemini API)
Invalid API key. Check your `.env`:
```bash
cat .env | grep GEMINI_API_KEY
```

#### WhatsApp Disconnects After Some Time
This is normal. The bot will auto-reconnect. Check logs:
```bash
tail -f logs/whatsapp.log
```

#### QR Code Expired
Simply restart the WhatsApp bot:
```bash
pkill -f "node bot.js"
./start-whatsapp.sh
```

### Getting Help

1. Check logs: `tail -f logs/*.log`
2. Verify all services are running: `ps aux | grep -E "uvicorn|node bot"`
3. Test backend health: `curl http://localhost:8000/health`
4. Check environment variables are set correctly
5. Review [WhatsApp bot README](whatsapp-bot/README.md) for detailed troubleshooting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **Agricultural Data**: MoFA Ghana, Yara Ghana, CSIR-CRI
- **AI/ML**: Google Gemini, scikit-learn
- **Frameworks**: FastAPI (Python), whatsapp-web.js (Node.js)
- **Inspired by**: The need to support Ghanaian farmers with accessible, affordable technology
- **Special Thanks**: Extension officers and farmers who provided feedback on agricultural content

## Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/kuapa-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/kuapa-ai/discussions)
- **Email**: support@kuapa-ai.com (if applicable)

## Roadmap

### Phase 1 (Current) ✅
- WhatsApp bot integration
- Google Gemini LLM
- Basic RAG with TF-IDF
- 61+ agricultural Q&As

### Phase 2 (Next)
- Twi language support
- Voice message handling
- Expanded knowledge base (500+ Q&As)
- User analytics

### Phase 3 (Future)
- Image-based crop disease diagnosis
- Weather integration
- Market price information
- pgVector semantic search
- Multi-language support (Ga, Ewe, Dagbani)

---

**Built with ❤️ for Ghanaian farmers**
