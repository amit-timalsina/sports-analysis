from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.websocket.manager import connection_manager
import json
import logging
from services.voice_processing import handle_complete_audio_processing

logger = logging.getLogger(__name__)

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

