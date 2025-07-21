"""Core application routes."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies.security import get_current_user
from auth.schemas.user import User as UserGet
from common.config.settings import settings
from common.schemas import SuccessResponse
from database.session import get_session

router = APIRouter(tags=["core"])


@router.get("/", response_class=HTMLResponse)
async def serve_index() -> HTMLResponse:
    """Serve the authentication page as the main entry point."""

    static_path = Path("static")
    html_file = static_path / "authentication.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    return HTMLResponse(content="basic login page")


@router.get("/home", response_class=HTMLResponse)
async def root(
    current_user: Annotated[UserGet, Depends(get_current_user)],
) -> HTMLResponse:
    """Serve the main web interface."""

    static_path = Path("static")
    html_file = static_path / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)

    return HTMLResponse(
        content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>{settings.app.title}</title></head>
    <body>
        <h1>🏏 {settings.app.title}</h1>
        <p> current_user: {current_user.id}</p>
        <p>Environment: {settings.app.environment}</p>
        <p>Version: {settings.app.version}</p>
        <p>Setting up the interface...</p>
    </body>
    </html>
    """,
        status_code=200,
    )


@router.get("/api")
async def api_info(session: Annotated[AsyncSession, Depends(get_session)]) -> SuccessResponse:
    """Information endpoint with database test."""
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        db_test = f"Database test successful: {row[0] if row else 'No result'}"
    except Exception as db_error:
        db_test = f"Database test failed: {type(db_error).__name__}: {db_error!s}"

    return SuccessResponse(
        message="Cricket Fitness Tracker API API",
        data={
            "version": "1.0.0",
            "environment": settings.app.environment,
            "status": "running",
            "database_test": db_test,
            "endpoints": {
                "voice_websocket": "/ws/voice/{session_id}",
                "health_check": "/health",
                "create_session": "/api/sessions",
                "audio_stats": "/api/audio/stats",
            },
        },
    )


@router.get("/api/test-db")
async def test_database_connection(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Test basic database connectivity."""
    try:
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        return {
            "status": "success",
            "message": f"Database connection test successful: {row[0] if row else None}",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database test failed: {type(e).__name__}: {e!s}",
        }
