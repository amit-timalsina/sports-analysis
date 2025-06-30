"""Cricket tracking database models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel


class CricketSessionType(str, Enum):
    """Types of cricket coaching sessions."""

    BATTING_DRILLS = "batting_drills"
    WICKET_KEEPING = "wicket_keeping"
    NETTING = "netting"
    PERSONAL_COACHING = "personal_coaching"
    TEAM_PRACTICE = "team_practice"
    OTHER = "other"


class MatchType(str, Enum):
    """Types of cricket matches."""

    PRACTICE = "practice"
    TOURNAMENT = "tournament"
    SCHOOL = "school"
    CLUB = "club"
    OTHER = "other"


class RestType(str, Enum):
    """Types of rest days."""

    COMPLETE_REST = "complete_rest"
    ACTIVE_RECOVERY = "active_recovery"
    INJURY_RECOVERY = "injury_recovery"


class CricketCoachingEntry(SQLModel, table=True):
    """Database model for cricket coaching session entries."""

    __tablename__ = "cricket_coaching_entries"

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

    # Cricket coaching specific fields
    session_type: CricketSessionType = Field(description="Type of cricket session")
    duration_minutes: int = Field(gt=0, description="Duration in minutes")
    what_went_well: str = Field(description="What went well in the session")
    areas_for_improvement: str = Field(description="Areas that need improvement")
    coach_feedback: str | None = Field(default=None, description="Coach feedback if available")
    self_assessment_score: int = Field(ge=1, le=10, description="Self-assessment score 1-10")

    # Technical focus areas
    skills_practiced: str = Field(description="Skills practiced during session")
    difficulty_level: int = Field(ge=1, le=10, description="Difficulty level of exercises")

    # Mental state during session
    confidence_level: int = Field(ge=1, le=10, description="Confidence level during session")
    focus_level: int = Field(ge=1, le=10, description="Focus level during session")
    learning_satisfaction: int = Field(ge=1, le=10, description="Learning satisfaction")
    mental_state: str = Field(description="Mental state during activity")
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


class CricketMatchEntry(SQLModel, table=True):
    """Database model for cricket match performance entries."""

    __tablename__ = "cricket_match_entries"

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

    # Match context
    match_type: MatchType = Field(description="Type of match")
    opposition_strength: int = Field(ge=1, le=10, description="Opposition strength 1-10")

    # Batting statistics
    runs_scored: int | None = Field(default=None, ge=0, description="Runs scored")
    balls_faced: int | None = Field(default=None, ge=0, description="Balls faced")
    boundaries_4s: int | None = Field(default=None, ge=0, description="4s scored")
    boundaries_6s: int | None = Field(default=None, ge=0, description="6s scored")
    how_out: str | None = Field(default=None, description="How out (if applicable)")
    key_shots_played: str | None = Field(default=None, description="Key shots played well")

    # Wicket keeping statistics
    catches_taken: int | None = Field(default=None, ge=0, description="Catches taken")
    catches_dropped: int | None = Field(default=None, ge=0, description="Catches dropped")
    stumpings: int | None = Field(default=None, ge=0, description="Stumpings completed")

    # Mental state tracking
    pre_match_nerves: int = Field(ge=1, le=10, description="Pre-match nerves level")
    post_match_satisfaction: int = Field(ge=1, le=10, description="Post-match satisfaction")
    mental_state: str = Field(description="Mental state during activity")
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


class RestDayEntry(SQLModel, table=True):
    """Database model for rest day entries."""

    __tablename__ = "rest_day_entries"

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

    # Rest day specific fields
    rest_type: RestType = Field(description="Type of rest day")
    physical_state: str = Field(description="Physical state during rest")
    fatigue_level: int = Field(ge=1, le=10, description="Fatigue level 1-10")
    energy_level: int = Field(ge=1, le=10, description="Energy level 1-10")
    motivation_level: int = Field(ge=1, le=10, description="Motivation level 1-10")
    mood_description: str = Field(description="Mood description")
    mental_state: str = Field(description="Mental state during activity")

    # Optional fields
    soreness_level: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Muscle soreness level 1-10",
    )
    training_reflections: str | None = Field(default=None, description="Reflections on training")
    goals_concerns: str | None = Field(default=None, description="Goals and concerns")
    recovery_activities: str | None = Field(default=None, description="Recovery activities done")
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
