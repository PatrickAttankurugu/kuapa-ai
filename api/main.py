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
from .config import GEMINI_API_KEY, DATABASE_URL
from .asr_whisper_api import transcribe_audio
from .rag import retrieve_context
from .llm import answer
from .tts_en_google import synthesize_en
from .database import init_db, close_db, get_db_context
from .user_service import UserService

# Constants
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_DURATION = 180  # 3 minutes in seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set - LLM functionality will be limited")
    else:
        logger.info("Kuapa AI starting up with Gemini integration")
    
    # Initialize database
    if DATABASE_URL:
        if init_db():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed - running without database")
    else:
        logger.warning("DATABASE_URL not set - running without database")

    media_out = Path("media/out")
    media_out.mkdir(parents=True, exist_ok=True)
    logger.info("Media directory initialized")

    yield

    # Cleanup
    close_db()
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
    phone_number: Optional[str] = None
    user_name: Optional[str] = None

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
        logger.info(
            f"Chat request received",
            extra={
                "request_id": request_id,
                "phone_number": request.phone_number,
                "has_user_info": bool(request.phone_number)
            }
        )

        rag_start = time.time()
        ctx = retrieve_context(request.message)
        rag_ms = int((time.time() - rag_start) * 1000)
        logger.info(f"RAG retrieved {len(ctx)} context chunks", extra={"request_id": request_id})

        llm_start = time.time()
        response_text = await answer(request.message, ctx)
        llm_ms = int((time.time() - llm_start) * 1000)

        total_ms = int((time.time() - start) * 1000)

        # Save to database if phone number provided
        if request.phone_number and DATABASE_URL:
            try:
                with get_db_context() as db:
                    if db:
                        # Get or create user
                        user = UserService.get_or_create_user(
                            db,
                            phone_number=request.phone_number,
                            name=request.user_name
                        )
                        
                        # Get or create conversation
                        conversation = UserService.get_or_create_conversation(db, user.id)
                        
                        # Save incoming message
                        UserService.save_message(
                            db=db,
                            user_id=user.id,
                            conversation_id=conversation.id,
                            content=request.message,
                            direction="incoming",
                            message_type="text",
                            language="en"
                        )
                        
                        # Save outgoing response
                        UserService.save_message(
                            db=db,
                            user_id=user.id,
                            conversation_id=conversation.id,
                            content=response_text,
                            direction="outgoing",
                            message_type="text",
                            language="en"
                        )
                        
                        logger.info(
                            f"Messages saved to database",
                            extra={"request_id": request_id, "user_id": str(user.id)}
                        )
            except Exception as db_error:
                logger.error(
                    f"Error saving to database: {str(db_error)}",
                    extra={"request_id": request_id},
                    exc_info=True
                )
                # Don't fail the request if database save fails

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
async def process_voice(
    file: UploadFile = File(...),
    phone_number: Optional[str] = None,
    user_name: Optional[str] = None
):
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
            extra={
                "request_id": request_id,
                "phone_number": phone_number,
                "has_user_info": bool(phone_number)
            }
        )

        # Validate file type (handle content types with codecs like "audio/ogg; codecs=opus")
        allowed_types = [
            'audio/ogg', 'audio/mpeg', 'audio/wav', 'audio/x-wav',
            'audio/mp3', 'audio/mp4', 'audio/m4a', 'audio/x-m4a',
            'audio/aac', 'audio/flac', 'audio/webm'
        ]
        
        # Extract base content type (remove codecs and other parameters)
        base_content_type = file.content_type.split(';')[0].strip() if file.content_type else ''
        
        if file.content_type and base_content_type not in allowed_types:
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

        # Save to database if phone number provided
        if phone_number and DATABASE_URL:
            try:
                with get_db_context() as db:
                    if db:
                        # Get or create user
                        user = UserService.get_or_create_user(
                            db,
                            phone_number=phone_number,
                            name=user_name
                        )
                        
                        # Get or create conversation
                        conversation = UserService.get_or_create_conversation(db, user.id)
                        
                        # Save incoming voice message with transcription
                        UserService.save_message(
                            db=db,
                            user_id=user.id,
                            conversation_id=conversation.id,
                            content=response_text,  # Store AI response in content
                            transcribed_text=transcribed_text,  # Store transcription separately
                            direction="incoming",
                            message_type="voice",
                            language=detected_language,
                            audio_file_path=file.filename
                        )
                        
                        # Save outgoing response
                        UserService.save_message(
                            db=db,
                            user_id=user.id,
                            conversation_id=conversation.id,
                            content=response_text,
                            direction="outgoing",
                            message_type="text",
                            language=detected_language
                        )
                        
                        logger.info(
                            f"Voice messages saved to database",
                            extra={"request_id": request_id, "user_id": str(user.id)}
                        )
            except Exception as db_error:
                logger.error(
                    f"Error saving voice to database: {str(db_error)}",
                    extra={"request_id": request_id},
                    exc_info=True
                )
                # Don't fail the request if database save fails

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

# User Management Endpoints

@app.get("/users")
async def list_users(limit: int = 10, offset: int = 0):
    """
    List all users in the database
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        with get_db_context() as db:
            if not db:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            from .models import User
            users = db.query(User).offset(offset).limit(limit).all()
            
            return {
                "users": [user.to_dict() for user in users],
                "count": len(users),
                "offset": offset,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.get("/users/{phone_number}")
async def get_user(phone_number: str):
    """
    Get user details by phone number
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        with get_db_context() as db:
            if not db:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            from .models import User
            user = db.query(User).filter(User.phone_number == phone_number).first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get user stats
            stats = UserService.get_user_stats(db, user.id)
            
            return {
                "user": user.to_dict(),
                "stats": stats
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.get("/users/{phone_number}/messages")
async def get_user_messages(phone_number: str, limit: int = 20):
    """
    Get conversation history for a user
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        with get_db_context() as db:
            if not db:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            from .models import User
            user = db.query(User).filter(User.phone_number == phone_number).first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            messages = UserService.get_conversation_history(db, user.id, limit=limit)
            
            return {
                "phone_number": phone_number,
                "messages": [msg.to_dict() for msg in messages],
                "count": len(messages)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@app.get("/stats")
async def get_overall_stats():
    """
    Get overall system statistics
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        with get_db_context() as db:
            if not db:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            from .models import User, Message, Conversation
            from sqlalchemy import func
            
            total_users = db.query(User).count()
            total_messages = db.query(Message).count()
            total_conversations = db.query(Conversation).count()
            voice_messages = db.query(Message).filter(Message.message_type == "voice").count()
            text_messages = db.query(Message).filter(Message.message_type == "text").count()
            
            # Get language distribution
            language_dist = db.query(
                Message.language,
                func.count(Message.id)
            ).group_by(Message.language).all()
            
            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "total_conversations": total_conversations,
                "message_types": {
                    "voice": voice_messages,
                    "text": text_messages
                },
                "languages": {
                    lang: count for lang, count in language_dist
                }
            }
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/health/db")
async def database_health():
    """
    Check database connection health
    """
    from .database import check_db_health
    
    if not DATABASE_URL:
        return {
            "status": "disabled",
            "message": "Database not configured"
        }
    
    is_healthy = check_db_health()
    
    if is_healthy:
        return {
            "status": "healthy",
            "database": "kuapa_ai",
            "connection": "active"
        }
    else:
        return {
            "status": "unhealthy",
            "message": "Database connection failed"
        }

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
