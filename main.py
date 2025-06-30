"""
Cricket Fitness Tracker FastAPI Application - Refactored.

Clean architecture with feature-based organization:
- Modern lifespan management with Pydantic settings
- Feature-based package structure
- Dependency injection and clean separation of concerns
- Comprehensive error handling and logging
"""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langfuse import observe
from pydantic import ValidationError

from common.config.settings import settings
from common.exceptions import AppError
from common.schemas import ErrorResponse, HealthResponse, SuccessResponse
from database.config.engine import sessionmanager
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.audio_storage import audio_storage
from voice_processing.services.openai_service import openai_service
from voice_processing.websocket.manager import connection_manager

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.app.log_file)
        if not settings.app.is_testing
        else logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Modern FastAPI lifespan management using Pydantic settings.

    Handles startup and shutdown of all services and resources.
    """
    logger.info("🚀 Starting Cricket Fitness Tracker application...")
    logger.info("Environment: %s", settings.app.environment)
    logger.info("Debug mode: %s", settings.app.debug)

    try:
        # Initialize database with settings
        logger.info("🔧 Initializing database...")
        sessionmanager.init_db()

        # Create tables if in development
        if settings.app.is_development:
            await sessionmanager.create_tables()

        logger.info("✅ Database initialized successfully")

        # Initialize audio storage using settings
        logger.info("🔧 Initializing audio storage...")
        audio_storage.ensure_storage_directories()
        logger.info("✅ Audio storage: %s", audio_storage.base_path.absolute())

        # Application is ready
        logger.info("🎯 Cricket Fitness Tracker is ready!")
        logger.info("📊 Database: %s:%s", settings.database.host, settings.database.port)
        logger.info("🌐 Server: %s:%s", settings.app.host, settings.app.port)

        yield  # Application runs here

    except Exception as e:
        logger.exception("❌ Failed to start application")
        startup_error = f"Application startup failed: {e}"
        raise AppError(startup_error) from e
    finally:
        # Cleanup on shutdown
        logger.info("🛑 Shutting down Cricket Fitness Tracker...")
        try:
            await connection_manager.cleanup()
            await sessionmanager.close()
            logger.info("✅ Cleanup completed successfully")
        except Exception:
            logger.exception("❌ Error during cleanup")


# Create FastAPI app with settings-based configuration
app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    lifespan=app_lifespan,
    docs_url="/api/docs" if not settings.app.is_production else None,
    redoc_url="/api/redoc" if not settings.app.is_production else None,
    debug=settings.app.debug,
)

# CORS middleware with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Handle application-specific errors."""
    logger.error("Application error: %s", exc.message)
    return JSONResponse(
        status_code=exc.code,
        content=ErrorResponse(
            error="application_error",
            message=exc.message,
            details=exc.details if hasattr(exc, "details") else None,
        ).model_dump(),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            message="Input validation failed",
            details={"validation_errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(500)
async def internal_server_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle internal server errors."""
    logger.exception("Internal server error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An internal server error occurred",
            details={"error_type": type(exc).__name__} if settings.app.debug else None,
        ).model_dump(),
    )


# Routes
@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main web interface."""
    html_file = static_path / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)

    return HTMLResponse(
        content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>{settings.app.title}</title></head>
    <body>
        <h1>🏏 {settings.app.title}</h1>
        <p>Environment: {settings.app.environment}</p>
        <p>Version: {settings.app.version}</p>
        <p>Setting up the interface...</p>
    </body>
    </html>
    """,
        status_code=200,
    )


@app.get("/api")
async def api_info() -> SuccessResponse:
    """Return basic application info."""
    return SuccessResponse(
        message=f"{settings.app.title} API",
        data={
            "version": settings.app.version,
            "environment": settings.app.environment,
            "status": "running",
            "endpoints": {
                "voice_websocket": "/ws/voice/{session_id}",
                "health_check": "/health",
                "create_session": "/api/sessions",
                "audio_stats": "/api/audio/stats",
            },
        },
    )


@app.get("/health")
async def health_check() -> HealthResponse:
    """Comprehensive health check endpoint."""
    try:
        # Get database statistics
        db_stats = await sessionmanager.get_stats()

        # Get WebSocket connection count
        ws_connections = connection_manager.get_connection_count()

        return HealthResponse(
            status="healthy",
            database=db_stats,
            websocket_connections=ws_connections,
            timestamp=f"{datetime.now(UTC).isoformat()}Z",
        )

    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


@app.post("/api/sessions")
async def create_session() -> SuccessResponse:
    """Create a new voice session."""
    session_id = str(uuid.uuid4())
    logger.info("Created new session: %s", session_id)

    return SuccessResponse(
        message="Session created successfully",
        data={
            "session_id": session_id,
            "websocket_url": f"/ws/voice/{session_id}",
            "status": "created",
            "settings": {
                "max_file_size_mb": settings.audio.max_file_size_mb,
                "supported_formats": settings.audio.supported_formats,
                "max_duration_seconds": settings.audio.max_duration_seconds,
            },
        },
    )


@app.get("/api/sessions/{session_id}")
async def get_session_info(session_id: str) -> SuccessResponse:
    """Get information about a specific session."""
    connection_info = connection_manager.get_connection_info(session_id)

    if not connection_info:
        raise HTTPException(status_code=404, detail="Session not found")

    return SuccessResponse(
        message="Session info retrieved",
        data=connection_info,
    )


@app.get("/api/audio/stats")
async def get_audio_storage_stats() -> SuccessResponse:
    """Get audio storage statistics."""
    try:
        stats = audio_storage.get_storage_stats()
        return SuccessResponse(
            message="Audio storage statistics",
            data=stats,
        )
    except Exception as e:
        logger.exception("Failed to get audio storage stats")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio stats") from e


@app.get("/api/audio/sessions/{session_id}")
async def get_session_audio_files(session_id: str) -> SuccessResponse:
    """Get audio files for a specific session."""
    try:
        files = audio_storage.get_session_audio_files(session_id)
        return SuccessResponse(
            message="Session audio files",
            data=files,
        )
    except Exception as e:
        logger.exception("Failed to get session audio files")
        raise HTTPException(status_code=500, detail="Failed to retrieve session audio files") from e


@app.websocket("/ws/voice/{session_id}")
@observe(capture_input=False, capture_output=False)
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """
    Modern WebSocket endpoint for real-time voice processing.

    Uses the new settings-based configuration and refactored services.
    """
    try:
        # Validate session ID - use constant for minimum length
        min_session_id_length = 8
        if not session_id or len(session_id) < min_session_id_length:
            await websocket.close(code=1008, reason="Invalid session ID")
            return

        # Accept connection through connection manager
        await connection_manager.connect(websocket, session_id)

        # Send welcome message with settings-based configuration
        welcome_message = WebSocketMessage(
            type="connection_established",
            session_id=session_id,
            data={
                "supported_entry_types": [
                    "fitness",
                    "cricket_coaching",
                    "cricket_match",
                    "rest_day",
                ],
                "max_message_size": settings.websocket.max_message_size,
                "ping_interval": settings.websocket.ping_interval,
                "audio_settings": {
                    "max_file_size_mb": settings.audio.max_file_size_mb,
                    "supported_formats": settings.audio.supported_formats,
                    "max_duration_seconds": settings.audio.max_duration_seconds,
                },
            },
        )
        await connection_manager.send_message(welcome_message, session_id)

        # Main message processing loop
        while True:
            try:
                # Receive message with size limit
                data = await websocket.receive()

                if data.get("type") == "websocket.disconnect":
                    break

                # Handle different message types
                if "text" in data:
                    await handle_text_message(session_id, data["text"])
                elif "bytes" in data:
                    await handle_voice_data(session_id, data["bytes"])

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for session: %s", session_id)
                break
            except Exception:
                logger.exception("Error processing WebSocket message")
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    error="message_processing_failed",
                    message="Failed to process WebSocket message",
                )
                try:
                    await connection_manager.send_message(error_message, session_id)
                except Exception:
                    break

    except Exception:
        logger.exception("WebSocket connection error for session %s", session_id)
    finally:
        connection_manager.disconnect(session_id)


async def handle_text_message(session_id: str, message: str) -> None:
    """Handle text messages from WebSocket client."""
    try:
        data = json.loads(message)
        message_type = data.get("type")

        if message_type == "ping":
            response = WebSocketMessage(
                type="pong",
                session_id=session_id,
            )
            await connection_manager.send_message(response, session_id)

        elif message_type == "session_info":
            response = WebSocketMessage(
                type="session_info",
                session_id=session_id,
                data={
                    "status": "active",
                    "settings": {
                        "max_duration": settings.audio.max_duration_seconds,
                        "supported_formats": settings.audio.supported_formats,
                    },
                },
            )
            await connection_manager.send_message(response, session_id)

        else:
            logger.warning("Unknown text message type: %s", message_type)

    except json.JSONDecodeError:
        logger.exception("Invalid JSON in text message")
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="invalid_json",
            message="Message must be valid JSON",
        )
        await connection_manager.send_message(error_message, session_id)


async def handle_voice_data(session_id: str, voice_data: bytes) -> None:
    """Process voice data using the refactored services."""
    try:
        start_time = datetime.now(UTC)

        # Send acknowledgment
        ack_message = WebSocketMessage(
            type="voice_received",
            session_id=session_id,
            data={
                "status": "processing",
                "audio_size": len(voice_data),
            },
        )
        await connection_manager.send_message(ack_message, session_id)

        # 1. Save raw audio using refactored audio storage
        logger.info("Processing voice data for session %s: %s bytes", session_id, len(voice_data))

        audio_save_result = await audio_storage.save_raw_audio(
            session_id=session_id,
            audio_data=voice_data,
            audio_format="webm",
        )

        # 2. Transcribe audio using refactored OpenAI service
        transcription_result = await openai_service.transcribe_audio(voice_data)

        # Send transcript to user for confirmation
        transcript_message = WebSocketMessage(
            type="transcript_ready",
            session_id=session_id,
            data={
                "transcript": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
            },
        )
        await connection_manager.send_message(transcript_message, session_id)

        # 3. Determine entry type and extract structured data
        entry_type = await openai_service.analyze_transcript_type(transcription_result.text)

        if entry_type == "fitness":
            structured_data = await openai_service.extract_fitness_data(transcription_result.text)
        else:
            # For now, default to fitness data structure
            structured_data = await openai_service.extract_fitness_data(transcription_result.text)

        processing_duration = (datetime.now(UTC) - start_time).total_seconds()

        # Send final result to client
        result_message = WebSocketMessage(
            type="voice_processed_complete",
            session_id=session_id,
            data={
                "status": "success",
                "entry_type": entry_type,
                "structured_data": structured_data,
                "audio_file": audio_save_result.get("filename"),
                "processing_time": processing_duration,
            },
        )
        await connection_manager.send_message(result_message, session_id)

        logger.info("✅ Complete voice processing successful for session %s", session_id)

    except Exception as e:
        logger.exception("Voice processing failed for session %s", session_id)
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="voice_processing_failed",
            message=str(e),
        )
        await connection_manager.send_message(error_message, session_id)


if __name__ == "__main__":
    # Development server configuration using settings
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload or settings.app.is_development,
        log_level=settings.app.log_level.lower(),
        # WebSocket optimizations from settings
        ws_ping_interval=settings.websocket.ping_interval,
        ws_ping_timeout=settings.websocket.ping_timeout,
        ws_max_size=settings.websocket.max_message_size,
    )
