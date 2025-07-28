"""Voice session management routes."""

import logging
import uuid

from fastapi import APIRouter, HTTPException

from common.config.settings import settings
from common.schemas import SuccessResponse
from voice_processing.websocket.manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice/sessions", tags=["voice-sessions"])


@router.post("")
async def create_session() -> SuccessResponse:
    """Create a new voice session."""
    session_id = str(uuid.uuid4())
    logger.info("Created new voice session: %s", session_id)

    return SuccessResponse(
        message="Voice session created successfully",
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


@router.get("/{session_id}")
async def get_session_info(session_id: str) -> SuccessResponse:
    """Get information about a specific voice session."""
    connection_info = connection_manager.get_connection_info(session_id)

    if not connection_info:
        raise HTTPException(status_code=404, detail="Voice session not found")

    return SuccessResponse(
        message="Voice session info retrieved",
        data=connection_info,
    )
