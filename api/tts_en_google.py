from typing import Dict
from gtts import gTTS
from pathlib import Path
from datetime import datetime

def synthesize_en(text: str) -> Dict[str, str]:
    media_out = Path("media/out")
    media_out.mkdir(parents=True, exist_ok=True)
    fn = media_out / f"reply_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.mp3"
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(str(fn))
    return {"audio_path": str(fn)}
