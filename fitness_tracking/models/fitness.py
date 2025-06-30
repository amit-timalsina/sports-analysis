"""Fitness tracking database models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel


class FitnessType(str, Enum):
    """Types of fitness activities."""

    RUNNING = "running"
    STRENGTH_TRAINING = "strength_training"
    CRICKET_SPECIFIC = "cricket_specific"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"


class Intensity(str, Enum):
    """Intensity levels for activities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FitnessEntry(SQLModel, table=True):
    """Database model for fitness activity entries."""

    __tablename__ = "fitness_entries"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # User and session info
    user_id: str = Field(index=True, description="User identifier")
    session_id: str = Field(index=True, description="Voice session identifier")

    # Voice processing metadata
    transcript: str = Field(description="Original voice transcript")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence in data extraction")
    processing_duration: float | None = Field(
        default=None,
        description="Time taken to process in seconds",
    )

    # Fitness activity data
    fitness_type: FitnessType = Field(description="Type of fitness activity")
    duration_minutes: int = Field(gt=0, description="Duration in minutes")
    intensity: Intensity = Field(description="Intensity level")
    details: str = Field(description="Activity details")
    mental_state: str = Field(description="Mental state during activity")
    energy_level: int = Field(ge=1, le=5, description="Energy level 1-5")

    # Optional metrics
    distance_km: float | None = Field(default=None, ge=0, description="Distance in kilometers")
    location: str | None = Field(default=None, description="Location of activity")
    notes: str | None = Field(default=None, description="Additional notes")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
