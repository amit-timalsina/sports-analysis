from services.message_handler import handle_text_message
from services.audio_handler import handle_audio_chunk
from voice_processing.websocket.manager import connection_manager
from fastapi import   WebSocket, WebSocketDisconnect
from voice_processing.schemas.processing import WebSocketMessage
from common.config.settings import settings
from langfuse import observe
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router =APIRouter(prefix='/ws/voice')

@router.websocket("/{session_id}")
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
