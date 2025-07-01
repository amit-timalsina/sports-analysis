from fastapi import APIRouter
from common.schemas import SuccessResponse
from common.config.settings import settings

router = APIRouter(prefix="/api",tags=['API Info'])

@router.get("")
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
