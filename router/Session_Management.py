from fastapi import APIRouter,HTTPException
from common.schemas import SuccessResponse
from common.config.settings import settings
from voice_processing.websocket.manager import connection_manager
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session",tags=['Session Management'])


@router.post("")
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


@router.get("/{session_id}")
async def get_session_info(session_id: str) -> SuccessResponse:
    """Get information about a specific session."""
    connection_info = connection_manager.get_connection_info(session_id)

    if not connection_info:
        raise HTTPException(status_code=404, detail="Session not found")

    return SuccessResponse(
        message="Session info retrieved",
        data=connection_info,
    )

