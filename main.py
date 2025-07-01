"""
Cricket Fitness Tracker FastAPI Application - Refactored.

Clean architecture with feature-based organization:
- Modern lifespan management with Pydantic settings
- Feature-based package structure
- Dependency injection and clean separation of concerns
- Comprehensive error handling and logging
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import  FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langfuse import observe
from pydantic import ValidationError

from common.config.settings import settings
from common.exceptions import AppError
from common.schemas import ErrorResponse
from database.config.engine import  sessionmanager

from voice_processing.services.audio_storage import audio_storage
from voice_processing.websocket.manager import connection_manager

from router import Session_Management,info,audio,entries,analytics,dashboard,health,websocket

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.app.log_file)
        if not settings.app.is_testing
        else logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Modern FastAPI lifespan management using Pydantic settings.

    Handles startup and shutdown of all services and resources.
    """
    logger.info("🚀 Starting Cricket Fitness Tracker application...")
    logger.info("Environment: %s", settings.app.environment)
    logger.info("Debug mode: %s", settings.app.debug)

    try:
        # Initialize database with settings
        logger.info("🔧 Initializing database...")
        sessionmanager.init_db()

        # Create tables if in development
        if settings.app.is_development:
            await sessionmanager.create_tables()

        logger.info("✅ Database initialized successfully")

        # Initialize audio storage using settings
        logger.info("🔧 Initializing audio storage...")
        audio_storage.ensure_storage_directories()
        logger.info("✅ Audio storage: %s", audio_storage.base_path.absolute())

        # Application is ready
        logger.info("🎯 Cricket Fitness Tracker is ready!")
        logger.info("📊 Database: %s:%s", settings.database.host, settings.database.port)
        logger.info("🌐 Server: %s:%s", settings.app.host, settings.app.port)

        yield  # Application runs here

    except Exception as e:
        logger.exception("❌ Failed to start application")
        startup_error = f"Application startup failed: {e}"
        raise AppError(startup_error) from e
    finally:
        # Cleanup on shutdown
        logger.info("🛑 Shutting down Cricket Fitness Tracker...")
        try:
            await connection_manager.cleanup()
            await sessionmanager.close()
            logger.info("✅ Cleanup completed successfully")
        except Exception:
            logger.exception("❌ Error during cleanup")


# Create FastAPI app with settings-based configuration
app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    lifespan=app_lifespan,
    docs_url="/api/docs" if not settings.app.is_production else None,
    redoc_url="/api/redoc" if not settings.app.is_production else None,
    debug=settings.app.debug,
)

# CORS middleware with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Handle application-specific errors."""
    logger.error("Application error: %s", exc.message)
    return JSONResponse(
        status_code=exc.code,
        content=ErrorResponse(
            error="application_error",
            message=exc.message,
            details=exc.details if hasattr(exc, "details") else None,
        ).model_dump(),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            message="Input validation failed",
            details={"validation_errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(500)
async def internal_server_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle internal server errors."""
    logger.exception("Internal server error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An internal server error occurred",
            details={"error_type": type(exc).__name__} if settings.app.debug else None,
        ).model_dump(),
    )


#  default Routes
@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main web interface."""
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
        <p>Environment: {settings.app.environment}</p>
        <p>Version: {settings.app.version}</p>
        <p>Setting up the interface...</p>
    </body>
    </html>
    """,
        status_code=200,
    )



app.include_router(info.router)
app.include_router(health.router)
app.include_router(Session_Management.router)
app.include_router(audio.router)
app.include_router(websocket.router)
app.include_router(entries.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)


if __name__ == "__main__":
    # Development server configuration using settings
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload or settings.app.is_development,
        log_level=settings.app.log_level.lower(),
        # WebSocket optimizations from settings
        ws_ping_interval=settings.websocket.ping_interval,
        ws_ping_timeout=settings.websocket.ping_timeout,
        ws_max_size=settings.websocket.max_message_size,
    )
