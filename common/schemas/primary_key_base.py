import uuid

from pydantic import BaseModel, Field


class PrimaryKeyBase(BaseModel):
    """Base Model for UUID-based primary key."""

    id: uuid.UUID = Field(..., description="Unique identifier for the record (Primary Key).")
