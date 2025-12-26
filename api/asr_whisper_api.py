import os
import time
import httpx
from typing import Dict

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

async def transcribe_wav(path: str) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        return {"text": "", "language": "en"}
    backoff = 1.0
    for attempt in range(5):
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f, "audio/wav")}
                data = {"model": OPENAI_TRANSCRIBE_MODEL}
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(f"{OPENAI_BASE_URL}/audio/transcriptions", headers=headers, data=data, files=files)
                    if resp.status_code >= 500 or resp.status_code == 429:
                        raise RuntimeError(f"upstream {resp.status_code}")
                    resp.raise_for_status()
                    j = resp.json()
                    return {"text": j.get("text", ""), "language": j.get("language", "en")}
        except Exception:
            if attempt == 4:
                return {"text": "", "language": "en"}
            time.sleep(backoff)
            backoff *= 2
