"""Schemas for activity entries with their conversation data."""

from pydantic import Field

from common.schemas.app_base_model import AppBaseModel
from fitness_tracking.schemas.cricket_coaching import CricketCoachingEntryRead
from fitness_tracking.schemas.cricket_match import CricketMatchEntryRead
from fitness_tracking.schemas.fitness import FitnessEntryRead
from fitness_tracking.schemas.rest_day import RestDayEntryRead
from voice_processing.schemas.conversation import ConversationRead


class ActivityWithConversationBase(AppBaseModel):
    """Base schema for activity entries with conversation data."""

    conversation: ConversationRead = Field(..., description="Related conversation data")


class FitnessEntryWithConversation(ActivityWithConversationBase):
    """Fitness entry with conversation data."""

    activity: FitnessEntryRead = Field(..., description="Fitness entry data")


class CricketCoachingEntryWithConversation(ActivityWithConversationBase):
    """Cricket coaching entry with conversation data."""

    activity: CricketCoachingEntryRead = Field(..., description="Cricket coaching entry data")


class CricketMatchEntryWithConversation(ActivityWithConversationBase):
    """Cricket match entry with conversation data."""

    activity: CricketMatchEntryRead = Field(..., description="Cricket match entry data")


class RestDayEntryWithConversation(ActivityWithConversationBase):
    """Rest day entry with conversation data."""

    activity: RestDayEntryRead = Field(..., description="Rest day entry data")


# Union type for all activities with conversation
ActivityWithConversation = (
    FitnessEntryWithConversation
    | CricketCoachingEntryWithConversation
    | CricketMatchEntryWithConversation
    | RestDayEntryWithConversation
)
