"""Audio management routes."""

import logging

from fastapi import APIRouter, HTTPException

from common.schemas import SuccessResponse
from voice_processing.services.audio_storage import audio_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/stats")
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


@router.get("/sessions/{session_id}")
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
