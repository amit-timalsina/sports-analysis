"""WebSocket routes for voice processing."""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from langfuse import observe
from sqlalchemy.ext.asyncio import AsyncSession

from common.config.settings import settings
from database.session import get_session
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
from voice_processing.schemas.conversation import ActivityType, ConversationResult
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.completion_service import ConversationCompletionService
from voice_processing.services.conversation_service import conversation_service
from voice_processing.services.openai_service import openai_service
from voice_processing.websocket.manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice/{session_id}")
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
