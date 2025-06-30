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
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langfuse import observe
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from common.config.settings import settings
from common.exceptions import AppError
from common.schemas import ErrorResponse, HealthResponse, SuccessResponse
from database.config.engine import get_database_session, sessionmanager
from fitness_tracking.repositories.cricket_repository import (
    CricketAnalyticsRepository,
    CricketCoachingRepository,
    CricketMatchRepository,
    RestDayRepository,
)
from fitness_tracking.repositories.fitness_repository import FitnessRepository
from voice_processing.schemas.conversation import ActivityType
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.audio_storage import audio_storage
from voice_processing.services.conversation_service import ConversationService
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
                "recording_instructions": {
                    "chunk_accumulation": True,
                    "completion_signal": "Send 'recording_complete' message to process accumulated audio",
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
                    # Accumulate audio chunks instead of processing immediately
                    await handle_audio_chunk(session_id, data["bytes"])

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
    """Handle text messages from WebSocket clients."""
    try:
        message_data = json.loads(message)
        message_type = message_data.get("type")

        if message_type == "voice_data_meta":
            # Store metadata for this session
            entry_type = message_data.get("entry_type")
            user_id = message_data.get("user_id", "demo_user")

            # Validate entry type
            valid_entry_types = ["fitness", "cricket_coaching", "cricket_match", "rest_day"]
            if entry_type not in valid_entry_types:
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    error="invalid_entry_type",
                    message=f"Invalid entry type. Must be one of: {valid_entry_types}",
                )
                await connection_manager.send_message(error_message, session_id)
                return

            # Store session metadata
            connection_manager.set_session_metadata(
                session_id,
                {
                    "entry_type": entry_type,
                    "user_id": user_id,
                },
            )

            # Acknowledge metadata received
            response = WebSocketMessage(
                type="voice_meta_received",
                session_id=session_id,
                data={
                    "entry_type": entry_type,
                    "user_id": user_id,
                    "ready_for_audio": True,
                },
            )
            await connection_manager.send_message(response, session_id)

        elif message_type == "recording_complete":
            # Process the accumulated audio when recording is complete
            logger.info("Received recording_complete signal for session %s", session_id)
            await handle_complete_audio_processing(session_id)

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


@observe(capture_input=True, capture_output=False)
async def handle_audio_chunk(session_id: str, audio_chunk: bytes) -> None:
    """Accumulate audio chunks for later processing when recording is complete."""
    try:
        # Validate audio chunk
        if len(audio_chunk) == 0:
            logger.debug("Received empty audio chunk for session %s", session_id)
            return

        # Check maximum individual chunk size to prevent abuse
        max_chunk_size = 2 * 1024 * 1024  # 2MB per chunk
        if len(audio_chunk) > max_chunk_size:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="audio_chunk_too_large",
                message=f"Audio chunk exceeds maximum size: {len(audio_chunk)} bytes",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Accumulate the audio chunk
        connection_manager.accumulate_audio_chunk(session_id, audio_chunk)
        total_size = len(connection_manager.get_accumulated_audio(session_id))

        # Check total accumulated size
        max_total_size = settings.audio.max_file_size_mb * 1024 * 1024
        if total_size > max_total_size:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="total_audio_too_large",
                message=f"Total accumulated audio exceeds maximum size: {total_size} bytes",
            )
            await connection_manager.send_message(error_message, session_id)
            # Clear the buffer to prevent further accumulation
            connection_manager.clear_audio_buffer(session_id)
            return

        # Send acknowledgment for chunk received
        chunk_ack = WebSocketMessage(
            type="audio_chunk_received",
            session_id=session_id,
            data={
                "chunk_size": len(audio_chunk),
                "total_accumulated": total_size,
                "status": "accumulated",
            },
        )
        await connection_manager.send_message(chunk_ack, session_id)

        logger.debug(
            "Accumulated audio chunk for session %s: +%d bytes (total: %d bytes)",
            session_id,
            len(audio_chunk),
            total_size,
        )

    except Exception as e:
        logger.exception("Audio chunk processing failed for session %s", session_id)
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="audio_chunk_processing_failed",
            message=str(e),
        )
        await connection_manager.send_message(error_message, session_id)


@observe(capture_input=True, capture_output=False)
async def handle_complete_audio_processing(session_id: str) -> None:
    """Process complete accumulated audio for a session using multi-turn conversation."""
    try:
        # Use the global connection_manager instance
        user_data = connection_manager.get_session_metadata(session_id)

        if not user_data:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="session_not_found",
                message="Session data not found",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        entry_type = user_data.get("entry_type")
        user_id = user_data.get("user_id", "demo_user")

        if not entry_type:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="missing_entry_type",
                message="Entry type not specified",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Get accumulated audio
        voice_data = connection_manager.get_accumulated_audio(session_id)
        if not voice_data:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="no_audio_data",
                message="No audio data found for processing",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        start_time = datetime.now(UTC)

        # Send processing start acknowledgment
        processing_message = WebSocketMessage(
            type="audio_processing_started",
            session_id=session_id,
            data={
                "status": "processing_complete_audio",
                "total_audio_size": len(voice_data),
                "entry_type": entry_type,
                "user_id": user_id,
            },
        )
        await connection_manager.send_message(processing_message, session_id)

        # 1. Save complete audio using refactored audio storage
        logger.info(
            "Processing complete audio for session %s: %s bytes, type: %s",
            session_id,
            len(voice_data),
            entry_type,
        )

        audio_save_result = await audio_storage.save_raw_audio(
            session_id=session_id,
            audio_data=voice_data,
            audio_format="webm",
        )

        # 2. Transcribe complete audio using improved OpenAI service
        transcription_result = await openai_service.transcribe_audio(voice_data)

        # Send transcript to user for confirmation
        transcript_message = WebSocketMessage(
            type="transcript_ready",
            session_id=session_id,
            data={
                "transcript": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
                "entry_type": entry_type,
            },
        )
        await connection_manager.send_message(transcript_message, session_id)

        # 3. **NEW**: Use conversation service for multi-turn processing with database session
        async with sessionmanager.get_session() as db_session:
            # Initialize conversation service with database session
            conversation_service_with_db = ConversationService(db_session=db_session)

            # Map entry_type to ActivityType
            activity_type_mapping = {
                "fitness": ActivityType.FITNESS,
                "cricket_coaching": ActivityType.CRICKET_COACHING,
                "cricket_match": ActivityType.CRICKET_MATCH,
                "rest_day": ActivityType.REST_DAY,
            }
            activity_type = activity_type_mapping.get(entry_type)

            if not activity_type:
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    error="invalid_activity_type",
                    message=f"Unsupported activity type: {entry_type}",
                )
                await connection_manager.send_message(error_message, session_id)
                return

            # Start or continue conversation
            conversation_context = conversation_service_with_db.get_conversation(session_id)
            if not conversation_context:
                # Start new conversation
                conversation_context = await conversation_service_with_db.start_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    activity_type=activity_type,
                )

                # Send conversation started message
                conversation_started_message = WebSocketMessage(
                    type="conversation_started",
                    session_id=session_id,
                    data={
                        "activity_type": activity_type.value,
                        "message": "I'll help you log your activity. Let's start with what you've told me and I'll ask follow-up questions to get all the details.",
                    },
                )
                await connection_manager.send_message(conversation_started_message, session_id)

            # Process user input and get conversation analysis
            conversation_analysis = await conversation_service_with_db.process_user_input(
                session_id=session_id,
                user_input=transcription_result.text,
                transcript_confidence=transcription_result.confidence,
            )

            # 4. Determine next step based on conversation analysis
            if conversation_analysis.should_continue and conversation_analysis.next_question:
                # Ask follow-up question
                follow_up_message = WebSocketMessage(
                    type="follow_up_question",
                    session_id=session_id,
                    data={
                        "question": conversation_analysis.next_question.question,
                        "field_target": conversation_analysis.next_question.field_target,
                        "question_type": conversation_analysis.next_question.question_type,
                        "priority": conversation_analysis.next_question.priority,
                        "turn_number": conversation_context.turn_count,
                        "completeness_score": conversation_analysis.data_completeness.completeness_score,
                        "collected_data": conversation_context.collected_data,
                        "missing_fields": conversation_analysis.data_completeness.missing_fields,
                        "instructions": "Please answer the question and then tap the microphone to record your response.",
                    },
                )
                await connection_manager.send_message(follow_up_message, session_id)

                logger.info(
                    "Sent follow-up question for session %s: %s (targeting field: %s)",
                    session_id,
                    conversation_analysis.next_question.question,
                    conversation_analysis.next_question.field_target,
                )

            elif conversation_analysis.can_generate_final_output:
                # Complete conversation and save to database
                conversation_result = conversation_service_with_db.complete_conversation(session_id)

                # Save final structured data to database
                structured_data = conversation_result.final_data
                saved_entry = None
                processing_duration = (datetime.now(UTC) - start_time).total_seconds()

                # Get all transcripts from the conversation context
                conversation_context = conversation_service_with_db.get_conversation(session_id)
                all_transcripts = ""
                if conversation_context and hasattr(conversation_context, "transcript_history"):
                    # Combine all transcripts with turn numbers
                    transcript_parts = []
                    for turn_data in conversation_context.transcript_history:
                        turn_num = (
                            turn_data.get("turn")
                            if isinstance(turn_data, dict)
                            else getattr(turn_data, "turn", "N/A")
                        )
                        transcript = (
                            turn_data.get("transcript")
                            if isinstance(turn_data, dict)
                            else getattr(turn_data, "transcript", "")
                        )
                        confidence = (
                            turn_data.get("confidence")
                            if isinstance(turn_data, dict)
                            else getattr(turn_data, "confidence", 0.0)
                        )
                        if transcript:
                            transcript_parts.append(
                                f"Turn {turn_num} (conf: {confidence:.2f}): {transcript}",
                            )
                    all_transcripts = "\n\n".join(transcript_parts)
                else:
                    # Fallback to final transcript if history not available
                    all_transcripts = transcription_result.text

                    # Save activity entry to respective table
                from typing import Any

                from fitness_tracking.repositories.cricket_repository import (
                    CricketCoachingRepository,
                    CricketMatchRepository,
                    RestDayRepository,
                )
                from fitness_tracking.repositories.fitness_repository import FitnessRepository

                saved_entry: Any = None
                if entry_type == "fitness":
                    fitness_repo = FitnessRepository(db_session)
                    saved_entry = await fitness_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "cricket_coaching":
                    cricket_repo = CricketCoachingRepository(db_session)
                    saved_entry = await cricket_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "cricket_match":
                    match_repo = CricketMatchRepository(db_session)
                    saved_entry = await match_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "rest_day":
                    rest_repo = RestDayRepository(db_session)
                    saved_entry = await rest_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                # **NEW**: Update conversation with related entry information
                if saved_entry and conversation_service_with_db.conversation_repo:
                    await conversation_service_with_db.conversation_repo.complete_conversation(
                        session_id=session_id,
                        result=conversation_result,
                        related_entry_id=saved_entry.id,
                        related_entry_type=entry_type,
                    )

                # Send conversation completed message
                result_message = WebSocketMessage(
                    type="conversation_completed",
                    session_id=session_id,
                    data={
                        "status": "success",
                        "entry_type": entry_type,
                        "structured_data": structured_data,
                        "saved_entry_id": saved_entry.id if saved_entry else None,
                        "audio_file": audio_save_result.get("filename"),
                        "total_turns": conversation_result.total_turns,
                        "data_quality_score": conversation_result.data_quality_score,
                        "conversation_efficiency": conversation_result.conversation_efficiency,
                        "processing_time": processing_duration,
                        "database_saved": saved_entry is not None,
                        "user_id": user_id,
                        "message": f"Great! I've saved your {entry_type.replace('_', ' ')} entry with {len(structured_data)} data points collected over {conversation_result.total_turns} turns.",
                    },
                )
                await connection_manager.send_message(result_message, session_id)

                logger.info(
                    "✅ Conversation completed for session %s: %d turns, %.2f quality, %.2f efficiency",
                    session_id,
                    conversation_result.total_turns,
                    conversation_result.data_quality_score,
                    conversation_result.conversation_efficiency,
                )

            else:
                # Error case - something went wrong
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    error="conversation_analysis_failed",
                    message=f"Conversation analysis failed: {conversation_analysis.reasoning}",
                )
                await connection_manager.send_message(error_message, session_id)
                conversation_service_with_db.cleanup_session(session_id)

        # Clear the audio buffer after processing
        connection_manager.clear_audio_buffer(session_id)

    except Exception as e:
        logger.exception("Complete audio processing failed for session %s", session_id)
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="voice_processing_failed",
            message=str(e),
        )
        await connection_manager.send_message(error_message, session_id)
        # Clean up on error
        connection_manager.clear_audio_buffer(session_id)
        if "conversation_service_with_db" in locals():
            conversation_service_with_db.cleanup_session(session_id)


@app.get("/api/entries/fitness")
async def get_fitness_entries(
    limit: int = 10,
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get recent fitness entries for a user."""
    try:
        fitness_repo = FitnessRepository(session)
        entries = await fitness_repo.get_recent_entries(
            user_id=user_id,
            limit=limit,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Fitness entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
                "days_back": days_back,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fitness entries: {e}",
        ) from e


@app.get("/api/entries/cricket/coaching")
async def get_cricket_coaching_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get cricket coaching session entries for a user."""
    try:
        cricket_repo = CricketCoachingRepository(session)
        entries = await cricket_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Cricket coaching entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket coaching entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cricket coaching entries: {e}",
        ) from e


@app.get("/api/entries/cricket/matches")
async def get_cricket_match_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get cricket match performance entries for a user."""
    try:
        match_repo = CricketMatchRepository(session)
        entries = await match_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Cricket match entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket match entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cricket match entries: {e}",
        ) from e


@app.get("/api/entries/rest-days")
async def get_rest_day_entries(
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get rest day entries for a user."""
    try:
        rest_repo = RestDayRepository(session)
        entries = await rest_repo.read_multi(limit=limit)

        return SuccessResponse(
            message="Rest day entries retrieved successfully",
            data={
                "entries": [entry.model_dump() for entry in entries],
                "total_count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rest day entries: {e}",
        ) from e


@app.get("/api/analytics/fitness")
async def get_fitness_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive fitness analytics for a user."""
    try:
        fitness_repo = FitnessRepository(session)
        analytics = await fitness_repo.get_fitness_analytics(
            user_id=user_id,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Fitness analytics generated successfully",
            data={
                "analytics": analytics.model_dump(),
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate fitness analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate fitness analytics: {e}",
        ) from e


@app.get("/api/analytics/cricket")
async def get_cricket_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive cricket analytics for a user."""
    try:
        cricket_analytics_repo = CricketAnalyticsRepository(session)
        analytics = await cricket_analytics_repo.get_cricket_analytics(
            user_id=user_id,
            days_back=days_back,
        )

        return SuccessResponse(
            message="Cricket analytics generated successfully",
            data={
                "analytics": analytics.model_dump(),
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate cricket analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate cricket analytics: {e}",
        ) from e


@app.get("/api/analytics/combined")
async def get_combined_analytics(
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get combined fitness and cricket analytics with correlations."""
    try:
        # Get both analytics
        fitness_repo = FitnessRepository(session)
        cricket_analytics_repo = CricketAnalyticsRepository(session)

        fitness_analytics = await fitness_repo.get_fitness_analytics(user_id, days_back)
        cricket_analytics = await cricket_analytics_repo.get_cricket_analytics(user_id, days_back)

        # Simple correlation analysis (could be enhanced)
        correlations = {}
        if fitness_analytics.weekly_frequency > 0 and cricket_analytics.average_self_assessment > 0:
            correlations["fitness_frequency_vs_cricket_confidence"] = min(
                fitness_analytics.weekly_frequency
                / 7
                * cricket_analytics.average_self_assessment
                / 10,
                1.0,
            )

        # Generate combined recommendations
        combined_recommendations = []
        combined_recommendations.extend(fitness_analytics.recommendations[:2])
        combined_recommendations.extend(cricket_analytics.recommendations[:2])

        if fitness_analytics.weekly_frequency < 3:
            combined_recommendations.append(
                "Increase fitness frequency to improve cricket performance correlation",
            )

        return SuccessResponse(
            message="Combined analytics generated successfully",
            data={
                "fitness_analytics": fitness_analytics.model_dump(),
                "cricket_analytics": cricket_analytics.model_dump(),
                "correlations": correlations,
                "combined_recommendations": combined_recommendations,
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to generate combined analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate combined analytics: {e}",
        ) from e


@app.get("/api/dashboard")
async def get_user_dashboard(
    user_id: str = "demo_user",  # TODO: Get from authentication
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive dashboard data for a user."""
    try:
        # Get recent entries from all types
        fitness_repo = FitnessRepository(session)
        cricket_coaching_repo = CricketCoachingRepository(session)
        cricket_match_repo = CricketMatchRepository(session)
        rest_repo = RestDayRepository(session)

        # Get recent data (last 7 days)
        recent_fitness = await fitness_repo.get_recent_entries(user_id, limit=5, days_back=7)
        recent_coaching = await cricket_coaching_repo.read_multi(limit=3)
        recent_matches = await cricket_match_repo.read_multi(limit=3)
        recent_rest = await rest_repo.read_multi(limit=3)

        # Get quick analytics
        fitness_analytics = await fitness_repo.get_fitness_analytics(user_id, days_back=7)

        # Activity summary for this week
        activity_summary = {
            "fitness_sessions": len(recent_fitness),
            "cricket_coaching_sessions": len(recent_coaching),
            "matches_played": len(recent_matches),
            "rest_days": len(recent_rest),
            "average_energy_level": fitness_analytics.average_energy_level,
            "weekly_frequency": fitness_analytics.weekly_frequency,
        }

        return SuccessResponse(
            message="Dashboard data retrieved successfully",
            data={
                "user_id": user_id,
                "activity_summary": activity_summary,
                "recent_entries": {
                    "fitness": [entry.model_dump() for entry in recent_fitness],
                    "cricket_coaching": [entry.model_dump() for entry in recent_coaching],
                    "cricket_matches": [entry.model_dump() for entry in recent_matches],
                    "rest_days": [entry.model_dump() for entry in recent_rest],
                },
                "quick_insights": {
                    "most_common_fitness_activity": fitness_analytics.most_common_activity,
                    "fitness_improvement_trends": fitness_analytics.improvement_trends,
                    "recommendations": fitness_analytics.recommendations[:3],
                },
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to get dashboard data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard data: {e}",
        ) from e


# **NEW**: Conversation Analytics Endpoints


@app.get("/api/conversations/analytics")
async def get_conversation_analytics(
    user_id: str = "demo_user",
    days_back: int = 30,
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get comprehensive conversation analytics for a user."""
    try:
        from voice_processing.repositories.conversation_repository import ConversationRepository

        conversation_repo = ConversationRepository(session)
        analytics = await conversation_repo.get_conversation_analytics(
            user_id=user_id,
            days=days_back,
        )

        return SuccessResponse(
            message="Conversation analytics retrieved successfully",
            data={
                "analytics": analytics,
                "user_id": user_id,
                "period_days": days_back,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        logger.exception("Failed to get conversation analytics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation analytics: {e}",
        ) from e


@app.get("/api/conversations/{session_id}")
async def get_conversation_details(
    session_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get detailed conversation history with all turns."""
    try:
        from voice_processing.repositories.conversation_repository import ConversationRepository

        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.get_conversation_by_session(session_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return SuccessResponse(
            message="Conversation details retrieved successfully",
            data={
                "conversation": {
                    "id": conversation.id,
                    "session_id": conversation.session_id,
                    "user_id": conversation.user_id,
                    "activity_type": conversation.activity_type,
                    "state": conversation.state,
                    "total_turns": conversation.total_turns,
                    "completion_status": conversation.completion_status,
                    "data_quality_score": conversation.data_quality_score,
                    "conversation_efficiency": conversation.conversation_efficiency,
                    "final_data": conversation.final_data,
                    "started_at": conversation.started_at.isoformat(),
                    "completed_at": conversation.completed_at.isoformat()
                    if conversation.completed_at
                    else None,
                    "total_duration_seconds": conversation.total_duration_seconds,
                    "related_entry_id": conversation.related_entry_id,
                    "related_entry_type": conversation.related_entry_type,
                },
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get conversation details")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation details: {e}",
        ) from e


@app.get("/api/conversations")
async def list_user_conversations(
    user_id: str = "demo_user",
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """List conversations for a user with pagination."""
    try:
        from voice_processing.repositories.conversation_repository import ConversationRepository

        conversation_repo = ConversationRepository(session)
        conversations = await conversation_repo.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        conversation_list = []
        for conv in conversations:
            conversation_list.append(
                {
                    "id": conv.id,
                    "session_id": conv.session_id,
                    "activity_type": conv.activity_type,
                    "state": conv.state,
                    "total_turns": conv.total_turns,
                    "completion_status": conv.completion_status,
                    "data_quality_score": conv.data_quality_score,
                    "conversation_efficiency": conv.conversation_efficiency,
                    "started_at": conv.started_at.isoformat(),
                    "completed_at": conv.completed_at.isoformat() if conv.completed_at else None,
                    "related_entry_id": conv.related_entry_id,
                    "related_entry_type": conv.related_entry_type,
                },
            )

        return SuccessResponse(
            message="User conversations retrieved successfully",
            data={
                "conversations": conversation_list,
                "total_count": len(conversation_list),
                "user_id": user_id,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(conversation_list) == limit,
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to list user conversations")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user conversations: {e}",
        ) from e


@app.get("/api/conversations/insights")
async def get_conversation_insights(
    user_id: str = "demo_user",
    activity_type: str | None = None,
    days_back: int = 30,
    session: AsyncSession = Depends(get_database_session),
) -> SuccessResponse:
    """Get conversation insights and question effectiveness."""
    try:
        from database.models.conversation import ActivityType as ModelActivityType
        from voice_processing.repositories.conversation_repository import ConversationRepository

        conversation_repo = ConversationRepository(session)

        # Get basic analytics
        analytics = await conversation_repo.get_conversation_analytics(
            user_id=user_id,
            days_back=days_back,
        )

        # Get most asked questions
        activity_filter = None
        if activity_type:
            try:
                activity_filter = ModelActivityType(activity_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid activity type: {activity_type}",
                )

        # Note: This would need to be implemented in the repository
        # most_asked_questions = await conversation_repo.get_most_asked_questions(
        #     activity_type=activity_filter,
        #     limit=10
        # )

        return SuccessResponse(
            message="Conversation insights retrieved successfully",
            data={
                "analytics": analytics,
                "insights": {
                    "most_effective_questions": [],  # Placeholder
                    "common_missing_fields": [],  # Placeholder
                    "conversation_patterns": {},  # Placeholder
                },
                "filters": {
                    "user_id": user_id,
                    "activity_type": activity_type,
                    "period_days": days_back,
                },
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get conversation insights")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation insights: {e}",
        ) from e


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
