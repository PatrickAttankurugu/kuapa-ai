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
from .config import OPENAI_API_KEY
from .asr_whisper_api import transcribe_wav
from .rag import retrieve_context
from .llm import answer
from .tts_en_google import synthesize_en

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set - LLM functionality will be limited")
    else:
        logger.info("Kuapa AI starting up with OpenAI integration")

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

@app.get("/")
async def root():
    return {
        "message": "Kuapa AI - Agricultural Advisory Assistant",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY)
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

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    request_id = str(uuid4())
    start = time.time()
    tmp = None

    try:
        logger.info(f"Audio request received", extra={"request_id": request_id})

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        asr_start = time.time()
        asr = await transcribe_wav(tmp.name)
        asr_ms = int((time.time() - asr_start) * 1000)

        text = asr.get("text", "").strip()
        if not text:
            logger.warning(f"No text transcribed from audio", extra={"request_id": request_id})
            return JSONResponse(content={
                "type": "text",
                "text": "Sorry, I couldn't understand the audio.",
                "request_id": request_id
            })

        logger.info(f"Transcribed text: {text[:100]}...", extra={"request_id": request_id})

        rag_start = time.time()
        ctx = retrieve_context(text)
        rag_ms = int((time.time() - rag_start) * 1000)

        llm_start = time.time()
        ans = await answer(text, ctx)
        llm_ms = int((time.time() - llm_start) * 1000)

        tts_start = time.time()
        tts = synthesize_en(ans)
        tts_ms = int((time.time() - tts_start) * 1000)

        total_ms = int((time.time() - start) * 1000)

        logger.info(
            f"Audio request completed",
            extra={"request_id": request_id, "duration_ms": total_ms}
        )

        return JSONResponse(content={
            "type": "audio",
            "audio_path": tts.get("audio_path"),
            "reply_lang": "en",
            "request_id": request_id,
            "timings_ms": {"asr": asr_ms, "rag": rag_ms, "llm": llm_ms, "tts": tts_ms, "total": total_ms}
        })

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", extra={"request_id": request_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

    finally:
        if tmp and os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {str(e)}")

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
