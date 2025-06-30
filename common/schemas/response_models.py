"""Response models for API endpoints using the user's patterns."""

from datetime import datetime
from typing import Any

from pydantic import Field

from common.schemas import AppBaseModel


class SuccessResponse(AppBaseModel):
    """Standard success response schema."""

    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")
    data: dict[str, Any] | None = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(AppBaseModel):
    """Standard error response schema."""

    success: bool = Field(default=False)
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(AppBaseModel):
    """Health check response model."""

    status: str
    database: dict[str, str]
    websocket_connections: int
    timestamp: str
