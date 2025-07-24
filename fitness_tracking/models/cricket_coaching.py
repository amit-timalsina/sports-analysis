from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.mixins.relationship_factories import user_relationship_factory
from common.models.activity import ActivityEntry
from fitness_tracking.schemas.enums.activity_type import ActivityType
from fitness_tracking.schemas.enums.coaching_focus_type import CoachingFocus
from fitness_tracking.schemas.enums.cricket_discipline_type import CricketDiscipline

if TYPE_CHECKING:
    from voice_processing.models.conversation import Conversation


class CricketCoachingEntry(
    ActivityEntry,
    user_relationship_factory(  # type: ignore[misc]
        back_populates="cricket_coaching_entries",
        ondelete="SET NULL",
        nullable=True,
    ),
):
    """Model for cricket coaching session entries."""

    __tablename__ = "cricket_coaching_entries"

    # Set the entry type
    activity_type: Mapped[ActivityType] = mapped_column(
        SA_Enum(ActivityType),
        default=ActivityType.CRICKET_COACHING,
        index=True,
    )

    # Core cricket fields (match DB schema)
    coach_name: Mapped[str] = mapped_column(String)
    session_type: Mapped[str] = mapped_column(String)
    duration_minutes: Mapped[int] = mapped_column()
    primary_focus: Mapped[CoachingFocus | None] = mapped_column(SA_Enum(CoachingFocus))
    secondary_focus: Mapped[CoachingFocus | None] = mapped_column(SA_Enum(CoachingFocus))
    skills_practiced: Mapped[list[str]] = mapped_column(JSON)
    discipline_focus: Mapped[CricketDiscipline | None] = mapped_column(SA_Enum(CricketDiscipline))

    # Session structure
    warm_up_minutes: Mapped[int | None] = mapped_column()
    skill_work_minutes: Mapped[int | None] = mapped_column()
    game_simulation_minutes: Mapped[int | None] = mapped_column()
    cool_down_minutes: Mapped[int | None] = mapped_column()

    # Equipment and setup
    equipment_used: Mapped[list[str] | None] = mapped_column(JSON)
    facility_name: Mapped[str | None] = mapped_column(String)
    indoor_outdoor: Mapped[str | None] = mapped_column(String)

    # Performance tracking
    technique_rating: Mapped[int | None] = mapped_column()
    effort_level: Mapped[int | None] = mapped_column()
    coach_feedback: Mapped[str | None] = mapped_column(String)
    improvement_areas: Mapped[list[str] | None] = mapped_column(JSON)

    # Goals and targets
    session_goals: Mapped[list[str] | None] = mapped_column(JSON)
    goals_achieved: Mapped[list[str] | None] = mapped_column(JSON)
    next_session_focus: Mapped[str | None] = mapped_column(String)

    # Cost and logistics
    session_cost: Mapped[float | None] = mapped_column()
    group_size: Mapped[int | None] = mapped_column()

    # Timing
    start_time: Mapped[time | None] = mapped_column()
    end_time: Mapped[time | None] = mapped_column()

    # relationship to conversation
    conversation: Mapped["Conversation"] = relationship(
        back_populates="cricket_coaching_entries",
    )
