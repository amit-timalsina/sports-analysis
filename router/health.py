from common.schemas import  HealthResponse
from database.config.engine import  sessionmanager
from voice_processing.websocket.manager import connection_manager
from datetime import UTC, datetime
import logging
from fastapi import APIRouter,HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/health',tags=['Health Check'])

@router.get("")
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