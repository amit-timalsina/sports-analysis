from pydantic import BaseModel, Field

from common.schemas.utc_datetime import UTCDateTime


class TimestampBase(BaseModel):
    """Base model for timestamp fields."""

    created_at: UTCDateTime = Field(..., description="Record creation timestamp.")
    updated_at: UTCDateTime = Field(..., description="Record update timestamp.")
