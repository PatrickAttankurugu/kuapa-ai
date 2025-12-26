import os

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.35"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Google TTS
GOOGLE_TTS_PROJECT_ID = os.getenv("GOOGLE_TTS_PROJECT_ID", "")
GOOGLE_TTS_CREDENTIALS_JSON_PATH = os.getenv("GOOGLE_TTS_CREDENTIALS_JSON_PATH", "")

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER = os.getenv("WHATSAPP_PHONE_NUMBER", "+233551087418")
PYTHON_API_URL = os.getenv("PYTHON_API_URL", "http://localhost:8000")

# Audio Processing
SUPPORTED_AUDIO_FORMATS = [
    'audio/ogg', 'audio/mpeg', 'audio/wav', 'audio/x-wav',
    'audio/mp3', 'audio/mp4', 'audio/m4a', 'audio/x-m4a',
    'audio/aac', 'audio/flac', 'audio/webm'
]

# Supported Languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'tw': 'Twi (Akan)',
    'ga': 'Ga',
    'ee': 'Ewe',
    'dag': 'Dagbani'
}
