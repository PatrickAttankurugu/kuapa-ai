from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import uuid4
from contextlib import asynccontextmanager
import time
import tempfile
import os
from pathlib import Path

from .logger import logger
from .config import GEMINI_API_KEY
from .asr_whisper_api import transcribe_audio
from .rag import retrieve_context
from .llm import answer
from .tts_en_google import synthesize_en

# Constants
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_DURATION = 180  # 3 minutes in seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set - LLM functionality will be limited")
    else:
        logger.info("Kuapa AI starting up with Gemini integration")

    media_out = Path("media/out")
    media_out.mkdir(parents=True, exist_ok=True)
    logger.info("Media directory initialized")

    yield

    logger.info("Kuapa AI shutting down")

app = FastAPI(
    title="Kuapa AI",
    description="Agricultural advisory assistant for farmers",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    request_id: str
    timings_ms: Dict[str, int]

class VoiceResponse(BaseModel):
    transcribed_text: str
    response: str
    language: str
    request_id: str
    timings_ms: Dict[str, int]
    metadata: Optional[Dict] = None

@app.get("/")
async def root():
    return {
        "message": "Kuapa AI - Agricultural Advisory Assistant",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "text_chat": True,
            "voice_messages": True,
            "twi_support": True,
            "multi_language": True
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "gemini_configured": bool(GEMINI_API_KEY),
        "features": {
            "voice_transcription": bool(GEMINI_API_KEY),
            "text_chat": True,
            "rag_retrieval": True
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    request_id = str(uuid4())
    start = time.time()

    try:
        logger.info(f"Chat request received", extra={"request_id": request_id})

        rag_start = time.time()
        ctx = retrieve_context(request.message)
        rag_ms = int((time.time() - rag_start) * 1000)
        logger.info(f"RAG retrieved {len(ctx)} context chunks", extra={"request_id": request_id})

        llm_start = time.time()
        response_text = await answer(request.message, ctx)
        llm_ms = int((time.time() - llm_start) * 1000)

        total_ms = int((time.time() - start) * 1000)

        logger.info(
            f"Chat request completed",
            extra={"request_id": request_id, "duration_ms": total_ms}
        )

        return ChatResponse(
            response=response_text,
            request_id=request_id,
            timings_ms={"rag": rag_ms, "llm": llm_ms, "total": total_ms}
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", extra={"request_id": request_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/process_voice")
async def process_voice(file: UploadFile = File(...)):
    """
    Process voice message from WhatsApp
    Supports: OGG, WAV, MP3, M4A and other audio formats
    Languages: English, Twi, Ga, Ewe, Dagbani
    Max size: 10MB
    """
    request_id = str(uuid4())
    start = time.time()
    tmp = None

    try:
        logger.info(
            f"Voice message received: {file.filename} ({file.content_type})",
            extra={"request_id": request_id}
        )

        # Validate file type
        allowed_types = [
            'audio/ogg', 'audio/mpeg', 'audio/wav', 'audio/x-wav',
            'audio/mp3', 'audio/mp4', 'audio/m4a', 'audio/x-m4a',
            'audio/aac', 'audio/flac', 'audio/webm'
        ]
        
        if file.content_type and file.content_type not in allowed_types:
            logger.warning(f"Unsupported audio format: {file.content_type}", extra={"request_id": request_id})
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file.content_type}. Supported: OGG, MP3, WAV, M4A, AAC, FLAC"
            )

        # Read and validate file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > MAX_AUDIO_SIZE:
            logger.warning(
                f"Audio file too large: {file_size / 1024 / 1024:.2f}MB",
                extra={"request_id": request_id}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large ({file_size / 1024 / 1024:.2f}MB). Maximum size is 10MB. Please send a shorter voice message."
            )
        
        logger.info(f"Audio file size: {file_size / 1024:.2f}KB", extra={"request_id": request_id})

        # Save uploaded file temporarily
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        logger.info(f"Audio file saved temporarily: {tmp.name}", extra={"request_id": request_id})

        # Transcribe audio
        asr_start = time.time()
        asr_result = await transcribe_audio(tmp.name)
        asr_ms = int((time.time() - asr_start) * 1000)

        transcribed_text = asr_result.get("text", "").strip()
        detected_language = asr_result.get("language", "en")
        transcription_error = asr_result.get("error")

        if transcription_error:
            logger.error(
                f"Transcription error: {transcription_error}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=400,
                content={
                    "transcribed_text": "",
                    "response": "Sorry, I couldn't understand the audio. Please try speaking more clearly or send a text message.",
                    "language": detected_language,
                    "request_id": request_id,
                    "error": transcription_error
                }
            )

        if not transcribed_text:
            logger.warning(f"No text transcribed from audio", extra={"request_id": request_id})
            return VoiceResponse(
                transcribed_text="",
                response="Sorry, I couldn't understand the audio. Please try again or send a text message.",
                language=detected_language,
                request_id=request_id,
                timings_ms={"asr": asr_ms, "total": int((time.time() - start) * 1000)}
            )

        logger.info(
            f"Transcription successful: '{transcribed_text[:100]}...' (language: {detected_language})",
            extra={"request_id": request_id}
        )

        # Retrieve context using RAG
        rag_start = time.time()
        ctx = retrieve_context(transcribed_text)
        rag_ms = int((time.time() - rag_start) * 1000)
        
        logger.info(f"RAG retrieved {len(ctx)} context chunks", extra={"request_id": request_id})

        # Generate response using LLM
        llm_start = time.time()
        response_text = await answer(transcribed_text, ctx, language=detected_language)
        llm_ms = int((time.time() - llm_start) * 1000)

        total_ms = int((time.time() - start) * 1000)

        logger.info(
            f"Voice message processed successfully",
            extra={
                "request_id": request_id,
                "duration_ms": total_ms,
                "language": detected_language,
                "transcription_length": len(transcribed_text)
            }
        )

        return VoiceResponse(
            transcribed_text=transcribed_text,
            response=response_text,
            language=detected_language,
            request_id=request_id,
            timings_ms={
                "asr": asr_ms,
                "rag": rag_ms,
                "llm": llm_ms,
                "total": total_ms
            },
            metadata={
                "detected_language": detected_language,
                "language_name": {
                    "en": "English",
                    "tw": "Twi",
                    "ga": "Ga",
                    "ee": "Ewe",
                    "dag": "Dagbani"
                }.get(detected_language, "Unknown"),
                "file_size_kb": round(file_size / 1024, 2)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing voice message: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error processing voice message: {str(e)}")

    finally:
        # Cleanup temporary file
        if tmp and os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
                logger.info(f"Cleaned up temporary file", extra={"request_id": request_id})
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {str(e)}")

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    """
    Legacy endpoint for audio processing
    Redirects to process_voice for consistency
    """
    return await process_voice(file)

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = Path("media/out") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WebSocket message from {client_id}: {data[:100]}")

            request_id = str(uuid4())
            start = time.time()

            try:
                rag_start = time.time()
                ctx = retrieve_context(data)
                rag_ms = int((time.time() - rag_start) * 1000)

                llm_start = time.time()
                response_text = await answer(data, ctx)
                llm_ms = int((time.time() - llm_start) * 1000)

                total_ms = int((time.time() - start) * 1000)

                import json
                response = json.dumps({
                    "response": response_text,
                    "request_id": request_id,
                    "timings_ms": {"rag": rag_ms, "llm": llm_ms, "total": total_ms}
                })

                await manager.send_message(response, client_id)

            except Exception as e:
                logger.error(f"Error in WebSocket processing: {str(e)}", exc_info=True)
                error_response = json.dumps({
                    "error": str(e),
                    "request_id": request_id
                })
                await manager.send_message(error_response, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/app")
    async def serve_app():
        return FileResponse(static_dir / "index.html")
