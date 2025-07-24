import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket
from requests import JSONDecodeError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories.user_repository import UserRepository
from common.config.settings import settings
from common.repositories.crud_repository import CRUDRepository
from database.session import get_session
from fitness_tracking.repositories.cricket_coaching_repository import CricketCoachingEntryRepository
from fitness_tracking.repositories.cricket_match_repository import CricketMatchEntryRepository
from fitness_tracking.repositories.fitness_repository import FitnessEntryRepository
from fitness_tracking.repositories.rest_day_repository import RestDayEntryRepository
from fitness_tracking.schemas.cricket_coaching import CricketCoachingEntryCreate
from fitness_tracking.schemas.cricket_match import CricketMatchEntryCreate
from fitness_tracking.schemas.enums.activity_type import ActivityType
from fitness_tracking.schemas.fitness import FitnessEntryCreate
from fitness_tracking.schemas.rest_day import RestDayEntryCreate
from logger import get_logger
from voice_processing.repositories.chat_message_repository import ChatMessageRepository
from voice_processing.repositories.conversation_repository import ConversationRepository
from voice_processing.schemas.chat_message import ChatMessageBase
from voice_processing.schemas.chat_message_sender import ChatMessageSender
from voice_processing.schemas.conversation import ConversationCreate
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.ai_service import AIService
from voice_processing.services.openai_service import OpenAIService
from voice_processing.websocket.manager import connection_manager

router = APIRouter(prefix="/api/voice_ws", tags=["voice_ws"])

logger = get_logger(__name__)


@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    Websocket endpoint which allows for real time communication between the client and server.

    The client sends audio chunks to the server, and the server processes them and
    sends the response back to the client.
    """
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

    while True:
        data = await websocket.receive()

        if data.get("type") == "websocket.disconnect":
            break

        if "text" in data:
            await handle_text_message(session_id, data["text"], db)

    connection_manager.disconnect(session_id)


async def handle_text_message(session_id: UUID, message: str, db: AsyncSession) -> None:
    """Handle text messages from WebSocket clients."""
    logger.debug("Received text message: %s", message)
    logger.debug("Session ID: %s", session_id)
    try:
        message_data = json.loads(message)
        message_type = message_data.get("type")
    except JSONDecodeError:
        logger.exception("Failed to parse message")
        return

    if message_type == "voice_data_meta":
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


async def handle_complete_audio_processing(session_id: UUID, db: AsyncSession) -> None:
    """Handle complete audio processing."""
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

    entry_type: str | None = session_metadata.get("entry_type")
    user_id: UUID | None = session_metadata.get("user_id")

    if not entry_type:
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="no_entry_type",
            message="No entry type found in session metadata",
        )
        await connection_manager.send_message(error_message, session_id)
        return

    if not user_id:
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="no_user_id",
            message="No user ID found in session metadata",
        )
        await connection_manager.send_message(error_message, session_id)
        return

    user_repository = UserRepository(db)
    user = await user_repository.read(user_id)

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
    openai_service = OpenAIService()
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

    conversation_respository = ConversationRepository(db)
    conversation = await conversation_respository.create(
        ConversationCreate(
            activity_type=ActivityType(entry_type),
        ),
        current_user=user,
    )

    # save transcript to conversation
    chat_message_repository = ChatMessageRepository(db)
    await chat_message_repository.create(
        ChatMessageBase(
            conversation_id=conversation.id,
            user_message=transcription_result.text,
            sender=ChatMessageSender.USER,
            is_read=True,
            is_completed=True,
        ),
    )

    # Send transcription completed message
    transcription_message = WebSocketMessage(
        type="transcription_completed",
        session_id=session_id,
        data={
            "transcription": transcription_result.text,
            "confidence": transcription_result.confidence,
            "duration": transcription_result.duration,
            "audio_size": len(audio_data),
            "entry_type": entry_type,
            "user_id": user_id,
        },
    )
    await connection_manager.send_message(transcription_message, session_id)

    # Process with conversation service
    logger.info("Starting conversation processing for session %s", session_id)
    activity_type_to_extraction_method = {
        ActivityType.CRICKET_MATCH: openai_service.extract_cricket_match_data,
        ActivityType.CRICKET_COACHING: openai_service.extract_cricket_coaching_data,
        ActivityType.REST_DAY: openai_service.extract_rest_day_data,
        ActivityType.FITNESS: openai_service.extract_fitness_data,
    }
    extraction_method = activity_type_to_extraction_method[conversation.activity_type]
    extracted_data = await extraction_method(transcription_result.text)
    logger.info("extracted_data: %s", extracted_data)

    # create ai
    ai_message = ChatMessageBase(
        conversation_id=conversation.id,
        sender=ChatMessageSender.AI,
        user_message=None,
        ai_extraction=extracted_data,
        is_read=True,
        is_completed=True,
    )
    ai_message_read = await chat_message_repository.create(ai_message)

    openai_client = openai_service.get_client()
    if not openai_client:
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="no_openai_client",
            message="No OpenAI client found",
        )
        await connection_manager.send_message(error_message, session_id)
        return
    ai_service = AIService(openai_client)
    follow_up_question = await ai_service.generate_follow_up_question(
        collected_data=extracted_data,
        activity_type=conversation.activity_type,
        user_message=transcription_result.text,
        model_name=settings.openai.gpt_model,
    )

    entry_type_model_factory = {
        ActivityType.CRICKET_MATCH: CricketMatchEntryCreate,
        ActivityType.CRICKET_COACHING: CricketCoachingEntryCreate,
        ActivityType.REST_DAY: RestDayEntryCreate,
        ActivityType.FITNESS: FitnessEntryCreate,
    }

    entry_type_repository_factory: dict[ActivityType, type[CRUDRepository]] = {
        ActivityType.CRICKET_MATCH: CricketMatchEntryRepository,
        ActivityType.CRICKET_COACHING: CricketCoachingEntryRepository,
        ActivityType.REST_DAY: RestDayEntryRepository,
        ActivityType.FITNESS: FitnessEntryRepository,
    }

    if not follow_up_question:
        # create entry in entry type model
        entry_type_model = entry_type_model_factory[conversation.activity_type]
        entry_type_repository = entry_type_repository_factory[conversation.activity_type]
        entry_type_repository_instance = entry_type_repository(db)
        entry_type_create = entry_type_model(
            user_id=user.id,
            activity_type=conversation.activity_type,
            **extracted_data,
        )
        await entry_type_repository_instance.create(entry_type_create, current_user=user)

        # send entry created message
        completed_message = WebSocketMessage(
            type="conversation_completed",
            session_id=session_id,
            data={
                **conversation.model_dump(),
                "entry_type": entry_type,
                "user_id": user_id,
                "entry_data": entry_type_create.model_dump(),
            },
        )
        await connection_manager.send_message(completed_message, session_id)

    # send follow up question to user
    follow_up_question_message = WebSocketMessage(
        type="follow_up_question",
        session_id=session_id,
        data={
            **follow_up_question.model_dump(),
        },
    )
    await connection_manager.send_message(follow_up_question_message, session_id)
