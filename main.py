"""
Sports Analysis - Cricket Fitness Tracker.

A modern FastAPI application for tracking cricket and fitness activities
through voice input using OpenAI's Whisper and GPT-4 for structured data extraction.

This application provides a comprehensive solution for athletes and fitness enthusiasts
to log their activities using natural voice commands, with automatic transcription
and intelligent data extraction.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import svcs
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from langfuse import observe  # type: ignore[import-untyped]
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.config.settings import settings
from common.exceptions import AppError
from common.schemas import SuccessResponse
from database.session import get_session
from dependency_injection import dependencies_registry, lifespan
from fitness_tracking.repositories import (
    CricketCoachingEntryRepository,
    CricketMatchEntryRepository,
    FitnessEntryRepository,
    RestDayEntryRepository,
)
from voice_processing.repositories.conversation_repository import (
    ConversationMessageRepository,
    ConversationRepository,
    ConversationTurnRepository,
)
from voice_processing.schemas.conversation import (
    ActivityType,
    ConversationResult,
)
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.audio_storage import audio_storage
from voice_processing.services.completion_service import ConversationCompletionService
from voice_processing.services.conversation_service import conversation_service
from voice_processing.services.openai_service import openai_service
from voice_processing.websocket.manager import connection_manager

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.app.log_file)
        if not settings.app.is_testing  # type: ignore[truthy-function]
        else logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# Create FastAPI app with settings-based configuration
app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    lifespan=svcs.fastapi.lifespan(lifespan=lifespan, registry=dependencies_registry),
    docs_url="/api/docs" if not settings.app.is_production else None,  # type: ignore[truthy-function]
    redoc_url="/api/redoc" if not settings.app.is_production else None,  # type: ignore[truthy-function]
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
async def app_error_handler(_request: Request, exc: AppError) -> PlainTextResponse:
    """Handle application-specific errors."""
    logger.error("Application error: %s", exc.message)
    return PlainTextResponse(
        status_code=exc.code,
        content=f"Application Error: {exc.message}",
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: ValidationError,
) -> PlainTextResponse:
    """Handle Pydantic validation errors."""
    logger.warning("Validation error: %s", exc)
    return PlainTextResponse(
        status_code=422,
        content="Validation Error: Input validation failed",
    )


@app.exception_handler(500)
async def internal_server_error_handler(_request: Request, exc: Exception) -> PlainTextResponse:
    """Handle internal server errors."""
    logger.exception("Internal server error")
    error_message = f"Internal Server Error: {type(exc).__name__}: {exc!s}"
    return PlainTextResponse(
        status_code=500,
        content=error_message,
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
async def api_info(session: Annotated[AsyncSession, Depends(get_session)]) -> SuccessResponse:
    """Information endpoint with database test."""
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        db_test = f"Database test successful: {row[0] if row else 'No result'}"
    except Exception as db_error:
        db_test = f"Database test failed: {type(db_error).__name__}: {db_error!s}"

    return SuccessResponse(
        message="Cricket Fitness Tracker API API",
        data={
            "version": "1.0.0",
            "environment": settings.app.environment,
            "status": "running",
            "database_test": db_test,
            "endpoints": {
                "voice_websocket": "/ws/voice/{session_id}",
                "health_check": "/health",
                "create_session": "/api/sessions",
                "audio_stats": "/api/audio/stats",
            },
        },
    )


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
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
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
                    "completion_signal": "Send 'recording_complete' message to process "
                    "accumulated audio",
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
                    await handle_text_message(session_id, data["text"], db)
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


async def handle_text_message(session_id: str, message: str, db: AsyncSession) -> None:
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
            await handle_complete_audio_processing(session_id, db)

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
async def handle_complete_audio_processing(session_id: str, db: AsyncSession) -> None:
    """Process complete accumulated audio with multi-turn conversation support."""
    try:
        start_time = datetime.now(UTC)

        # Get accumulated audio and metadata
        audio_data = connection_manager.get_accumulated_audio(session_id)
        session_metadata = connection_manager.get_session_metadata(session_id)

        if not audio_data:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="no_audio_data",
                message="No audio data accumulated for processing",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        if not session_metadata:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="no_session_metadata",
                message="No session metadata found. Please send voice_data_meta first.",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        entry_type = session_metadata.get("entry_type")
        user_id = session_metadata.get("user_id")

        # Send processing started message
        processing_message = WebSocketMessage(
            type="audio_processing_started",
            session_id=session_id,
            data={
                "audio_size": len(audio_data),
                "entry_type": entry_type,
                "user_id": user_id,
                "stage": "transcription",
            },
        )
        await connection_manager.send_message(processing_message, session_id)

        # Transcribe the complete audio
        logger.info("Starting transcription for session %s", session_id)
        transcription_result = await openai_service.transcribe_audio(audio_data)

        if not transcription_result or not transcription_result.text:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="transcription_failed",
                message="Audio transcription failed or returned empty",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Send transcription completed message
        transcription_message = WebSocketMessage(
            type="transcription_completed",
            session_id=session_id,
            data={
                "transcript": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
                "stage": "conversation_processing",
            },
        )
        await connection_manager.send_message(transcription_message, session_id)

        # Process with conversation service
        logger.info("Starting conversation processing for session %s", session_id)

        # Start conversation if it doesn't exist
        conversation_context = conversation_service.get_conversation(session_id)
        if not conversation_context:
            # Ensure user_id is a string
            user_id_str = user_id or "demo_user"
            conversation_context = conversation_service.start_conversation(
                session_id=session_id,
                user_id=user_id_str,
                activity_type=ActivityType(entry_type),
            )

        # Process the user input
        conversation_result = await conversation_service.process_user_input(
            session_id=session_id,
            user_input=transcription_result.text,
            transcript_confidence=transcription_result.confidence,
        )

        # If the conversation has gathered enough information or max turns reached,
        # finalise it and persist the final result.
        completed_conversation: ConversationResult | None = None
        saved_entry_id: int | None = None
        if conversation_result.can_generate_final_output:
            completed_conversation = conversation_service.complete_conversation(session_id)

            # Use completion service to persist all data
            try:
                completion_service = ConversationCompletionService(
                    conversation_repo=ConversationRepository(db),
                    message_repo=ConversationMessageRepository(db),
                    turn_repo=ConversationTurnRepository(db),
                    fitness_repo=FitnessEntryRepository(db),
                    cricket_repo=CricketMatchEntryRepository(db),
                    coaching_repo=CricketCoachingEntryRepository(db),
                    rest_repo=RestDayEntryRepository(db),
                )

                completion_result = await completion_service.complete_conversation(
                    conversation_result=completed_conversation,
                    transcript_history=conversation_context.transcript_history,
                    metadata=session_metadata,
                )

                saved_entry_id = completion_result.activity_id
                logger.info(
                    "Completed conversation %d with activity %d for session %s",
                    completion_result.conversation_id,
                    saved_entry_id,
                    session_id,
                )
            except Exception as e:
                logger.exception("Failed to complete conversation")
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    error="completion_failed",
                    message=f"Failed to complete conversation: {e!s}",
                )
                await connection_manager.send_message(error_message, session_id)

        # Send final result
        final_message = WebSocketMessage(
            type="conversation_processed",
            session_id=session_id,
            data={
                "conversation_result": conversation_result.model_dump(),
                "conversation_completed": completed_conversation.model_dump()
                if completed_conversation
                else None,
                "processing_duration": (datetime.now(UTC) - start_time).total_seconds(),
                # Indicate whether the conversation should continue so the frontend knows
                # to prompt the user for more input or finish the flow.
                "status": "in_progress" if conversation_result.should_continue else "completed",
            },
        )
        await connection_manager.send_message(final_message, session_id)

        # If we have completed the conversation, emit a separate message that the
        # frontend explicitly listens for.
        if completed_conversation is not None:
            completed_msg = WebSocketMessage(
                type="conversation_completed",
                session_id=session_id,
                data={
                    **completed_conversation.model_dump(),
                    # Include the saved entry ID if persistence succeeded
                    "saved_entry_id": saved_entry_id,
                    "message": (
                        "Conversation finished and saved successfully."
                        if saved_entry_id
                        else "Conversation finished but not yet saved."
                    ),
                },
            )
            await connection_manager.send_message(completed_msg, session_id)

        # Clear the audio buffer after successful processing
        connection_manager.clear_audio_buffer(session_id)

        logger.info(
            "Completed audio processing for session %s in %.2f seconds",
            session_id,
            (datetime.now(UTC) - start_time).total_seconds(),
        )

        if conversation_result.should_continue and conversation_result.next_question:
            # Build a richer payload to satisfy frontend expectations
            fq_payload = {
                **conversation_result.next_question.model_dump(),  # question, field_target, etc.
                "turn_number": conversation_context.turn_count,
                "completeness_score": conversation_result.data_completeness.confidence_score,
                "collected_data": conversation_context.collected_data,
                # Simple instructions for the user
                "instructions": "Answer the question briefly so we can log your activity.",
            }

            follow_up_msg = WebSocketMessage(
                type="follow_up_question",
                session_id=session_id,
                data=fq_payload,
            )
            await connection_manager.send_message(follow_up_msg, session_id)

    except Exception as e:
        logger.exception("Audio processing failed for session %s", session_id)
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="audio_processing_failed",
            message=str(e),
        )
        await connection_manager.send_message(error_message, session_id)
        # Clear the buffer on error to reset state
        connection_manager.clear_audio_buffer(session_id)


# API endpoints for data retrieval - using new clean architecture repositories
@app.get("/api/entries/fitness")
async def get_fitness_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent fitness entries using clean architecture repository."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=limit,
        )

        return SuccessResponse(
            message="Fitness entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
                "days_back": days_back,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness entries") from e


@app.get("/api/entries/cricket/coaching")
async def get_cricket_coaching_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent cricket coaching entries using clean architecture repository."""
    try:
        repository = CricketCoachingEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket coaching entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket coaching entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket coaching entries",
        ) from e


@app.get("/api/entries/cricket/matches")
async def get_cricket_match_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent cricket match entries using clean architecture repository."""
    try:
        repository = CricketMatchEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Cricket match entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket match entries")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cricket match entries",
        ) from e


@app.get("/api/entries/rest-days")
async def get_rest_day_entries(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 10,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get recent rest day entries using clean architecture repository."""
    try:
        repository = RestDayEntryRepository(session)
        entries = await repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=limit,
        )

        return SuccessResponse(
            message="Rest day entries retrieved successfully",
            data={
                "entries": [entry.model_dump(mode="json") for entry in entries],
                "count": len(entries),
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get rest day entries")
        raise HTTPException(status_code=500, detail="Failed to retrieve rest day entries") from e


@app.get("/api/analytics/fitness")
async def get_fitness_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get fitness analytics using clean architecture repository."""
    try:
        repository = FitnessEntryRepository(session)
        entries = await repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=1000,  # Get more data for analytics
        )

        # Basic analytics calculation
        total_sessions = len(entries)
        if total_sessions > 0:
            total_duration = sum(entry.duration_minutes for entry in entries)
            avg_duration = total_duration / total_sessions
            total_calories = sum(entry.calories_burned or 0 for entry in entries)
        else:
            total_duration = avg_duration = total_calories = 0

        return SuccessResponse(
            message="Fitness analytics retrieved successfully",
            data={
                "total_sessions": total_sessions,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": round(avg_duration, 1),
                "total_calories_burned": total_calories,
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get fitness analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve fitness analytics") from e


@app.get("/api/analytics/cricket")
async def get_cricket_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get cricket analytics using clean architecture repository."""
    try:
        match_repository = CricketMatchEntryRepository(session)

        # Get performance statistics
        stats = await match_repository.get_performance_stats(
            current_user=None,  # TODO: Pass actual user
        )

        return SuccessResponse(
            message="Cricket analytics retrieved successfully",
            data={
                **stats,
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get cricket analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve cricket analytics") from e


@app.get("/api/analytics/combined")
async def get_combined_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    days_back: int = 30,
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get combined analytics across all activity types using clean architecture repositories."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        match_repository = CricketMatchEntryRepository(session)

        # Get fitness data
        fitness_entries = await fitness_repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=days_back,
            limit=1000,
        )

        # Get cricket stats
        cricket_stats = await match_repository.get_performance_stats(
            current_user=None,  # TODO: Pass actual user
        )

        # Combined analytics
        total_fitness_sessions = len(fitness_entries)
        total_cricket_matches = cricket_stats.get("total_matches", 0)
        total_activities = total_fitness_sessions + total_cricket_matches

        if total_fitness_sessions > 0:
            total_fitness_duration = sum(entry.duration_minutes for entry in fitness_entries)
        else:
            total_fitness_duration = 0

        return SuccessResponse(
            message="Combined analytics retrieved successfully",
            data={
                "total_activities": total_activities,
                "fitness": {
                    "total_sessions": total_fitness_sessions,
                    "total_duration_minutes": total_fitness_duration,
                },
                "cricket": cricket_stats,
                "activity_breakdown": {
                    "fitness_percentage": round(
                        (total_fitness_sessions / total_activities * 100),
                        1,
                    )
                    if total_activities > 0
                    else 0,
                    "cricket_percentage": round((total_cricket_matches / total_activities * 100), 1)
                    if total_activities > 0
                    else 0,
                },
                "days_analyzed": days_back,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.exception("Failed to get combined analytics")
        raise HTTPException(status_code=500, detail="Failed to retrieve combined analytics") from e


@app.get("/api/dashboard")
async def get_user_dashboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: str = "demo_user",  # TODO: Get from authentication
) -> SuccessResponse:
    """Get comprehensive user dashboard data using clean architecture repositories."""
    try:
        fitness_repository = FitnessEntryRepository(session)
        coaching_repository = CricketCoachingEntryRepository(session)

        # Get recent entries (last 7 days for dashboard)
        recent_fitness = await fitness_repository.read_recent_entries(
            current_user=None,  # TODO: Pass actual user
            days=7,
            limit=20,
        )

        recent_coaching = await coaching_repository.read_multi(
            current_user=None,  # TODO: Pass actual user
            limit=10,
        )

        # Quick stats
        this_week_fitness = len(recent_fitness)
        this_week_coaching = len(recent_coaching)

        return SuccessResponse(
            message="Dashboard data retrieved successfully",
            data={
                "user_id": user_id,
                "this_week": {
                    "fitness_sessions": this_week_fitness,
                    "coaching_sessions": this_week_coaching,
                    "total_activities": this_week_fitness + this_week_coaching,
                },
                "recent_activities": {
                    "fitness": [entry.model_dump(mode="json") for entry in recent_fitness[:5]],
                    "coaching": [entry.model_dump(mode="json") for entry in recent_coaching[:5]],
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to get dashboard data")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data") from e


# Add a test endpoint before the other API endpoints
@app.get("/api/test-db")
async def test_database_connection(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlainTextResponse:
    """Test basic database connectivity."""
    try:
        # Simple query to test connection
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()

        return PlainTextResponse(
            status_code=200,
            content=f"Database connection test successful: {row[0] if row else None}",
        )
    except Exception as e:
        return PlainTextResponse(
            status_code=500,
            content=f"Database test failed: {type(e).__name__}: {e!s}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )
