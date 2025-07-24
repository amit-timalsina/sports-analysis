from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from langfuse import observe
from sqlalchemy.ext.asyncio import AsyncSession

from common.config.settings import settings
from database.session import get_session
from logger import get_logger
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.websocket.manager import connection_manager

logger = get_logger(__name__)


router = APIRouter(prefix="/api/websocket")


@router.websocket("/{session_id}")
@observe(capture_input=False, capture_output=False)
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """WebSocket endpoint for voice processing."""

    # Accept the WebSocket connection
    await connection_manager.connect(websocket, session_id)

    while True:
        try:
            data = await websocket.receive()
            if data.get("type") == "websocket.disconnect":
                break

            # if "text" in data:
            #     await handle_text_message(session_id, data["text"], session)

            if "bytes" in data:
                await handle_audio_chunk(session_id, data["bytes"], session)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
            break


async def handle_audio_chunk(session_id: str, audio_chunk: bytes) -> None:
    """Accumulate audio chunks for later processing when recording is complete."""
    try:
        if len(audio_chunk) > 0:
            logger.debug("Received empty audio chunk for session")
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
