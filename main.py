"""
Sports Analysis - Cricket Fitness Tracker.

A modern FastAPI application for tracking cricket and fitness activities
through voice input using OpenAI's Whisper and GPT-4 for structured data extraction.

This application provides a comprehensive solution for athletes and fitness enthusiasts
to log their activities using natural voice commands, with automatic transcription
and intelligent data extraction.
"""

import logging
from pathlib import Path

from fastapi import Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app_factory.factory import create_app
from common.config.settings import settings
from common.exceptions import AppError

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.app.log_file)
        if not settings.app.is_testing  # type: ignore[truthy-function]
        else logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


app = create_app()

# Mount static files
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> PlainTextResponse:
    """Handle application-specific errors."""
    logger.error("Application error: %s", exc.message)
    return PlainTextResponse(
        status_code=exc.code,
        content=f"Application Error: {exc.message}",
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: ValidationError,
) -> PlainTextResponse:
    """Handle Pydantic validation errors."""
    logger.warning("Validation error: %s", exc)
    return PlainTextResponse(
        status_code=422,
        content="Validation Error: Input validation failed",
    )


@app.exception_handler(500)
async def internal_server_error_handler(_request: Request, exc: Exception) -> PlainTextResponse:
    """Handle internal server errors."""
    logger.exception("Internal server error")
    error_message = f"Internal Server Error: {type(exc).__name__}: {exc!s}"
    return PlainTextResponse(
        status_code=500,
        content=error_message,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )
