# Kuapa AI - WhatsApp Bot

WhatsApp bot interface for Kuapa AI agricultural advisory system using `whatsapp-web.js`.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- Python backend running (see main README)
- Active phone number for WhatsApp bot (+233551087418)

### Installation

1. Install dependencies:
```bash
cd whatsapp-bot
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Configure `.env`:
```env
PYTHON_API_URL=http://localhost:8000
WHATSAPP_PHONE_NUMBER=+233551087418
SESSION_NAME=kuapa-ai-session
```

### Running the Bot

1. Start the Python backend (in main directory):
```bash
cd ..
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the WhatsApp bot (in whatsapp-bot directory):
```bash
npm start
```

3. **Scan QR Code**: A QR code will appear in the terminal. Scan it with your WhatsApp mobile app:
   - Open WhatsApp on your phone
   - Go to Settings → Linked Devices
   - Tap "Link a Device"
   - Scan the QR code from the terminal

4. Once authenticated, the bot is ready! Send messages to your bot number.

## 📱 Features

- **Automatic QR Authentication**: Scan once, stay logged in
- **Real-time Message Processing**: Instant responses via RAG + Gemini AI
- **Context-Aware**: Maintains conversation history
- **Error Handling**: Graceful error messages for users
- **Health Monitoring**: Built-in health checks
- **Special Commands**:
  - `/start` or `hi` - Welcome message
  - `/help` - Help information

## 🏗️ Architecture

```
WhatsApp User → WhatsApp Web.js Client → Node.js Bot → Python FastAPI Backend
                                                         ↓
                                                    RAG Retrieval (TF-IDF)
                                                         ↓
                                                    Gemini 2.5 Flash LLM
                                                         ↓
                                                    Response → WhatsApp User
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHON_API_URL` | Python backend URL | `http://localhost:8000` |
| `WHATSAPP_PHONE_NUMBER` | Bot's phone number | `+233551087418` |
| `SESSION_NAME` | Session identifier | `kuapa-ai-session` |

## 📝 Usage Examples

**User**: "How do I control fall armyworm?"
**Bot**: [Provides advice from agricultural knowledge base using RAG + Gemini]

**User**: "What are signs of nitrogen deficiency?"
**Bot**: [Retrieves context and generates accurate response]

## 🐛 Troubleshooting

### QR Code Not Showing
- Ensure terminal supports Unicode characters
- Try running with `--no-sandbox` flag
- Check Node.js version (18+ required)

### Authentication Fails
- Delete `.wwebjs_auth/` directory and try again
- Ensure WhatsApp mobile app is updated
- Check internet connection

### Backend Connection Errors
- Verify Python backend is running: `curl http://localhost:8000/health`
- Check `PYTHON_API_URL` in `.env`
- Check firewall settings

### Bot Not Responding
- Check Python backend logs for errors
- Verify Gemini API key is set in main `.env`
- Check message logs in terminal

## 🔒 Security Notes

- Keep `.wwebjs_auth/` directory private (contains session data)
- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Regularly update dependencies: `npm update`

## 📊 Monitoring

The bot logs:
- ✅ Successful message processing
- ❌ Errors and exceptions
- 💓 Health checks every 5 minutes
- 📩 Incoming messages with metadata

## 🛠️ Development

### Development Mode (with auto-reload)
```bash
npm run dev
```

### Testing Backend Connection
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I plant maize?"}'
```

## 📚 Dependencies

- **whatsapp-web.js**: WhatsApp Web client
- **qrcode-terminal**: QR code display in terminal
- **axios**: HTTP client for API calls
- **dotenv**: Environment variable management

## 🚀 Deployment

### Using PM2 (Recommended for production)

```bash
npm install -g pm2
pm2 start bot.js --name kuapa-whatsapp-bot
pm2 save
pm2 startup
```

### Using systemd

Create `/etc/systemd/system/kuapa-whatsapp-bot.service`:
```ini
[Unit]
Description=Kuapa AI WhatsApp Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/kuapa-ai/whatsapp-bot
ExecStart=/usr/bin/node bot.js
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable kuapa-whatsapp-bot
sudo systemctl start kuapa-whatsapp-bot
```

## 📄 License

MIT License - see main project LICENSE file
