"""Conversation related enums."""

from enum import Enum


class ConversationState(str, Enum):
    """State of a conversation in the voice processing flow."""

    STARTED = "started"
    COLLECTING_DATA = "collecting_data"
    ASKING_FOLLOWUP = "asking_followup"
    VALIDATING_DATA = "validating_data"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ResolutionStatus(str, Enum):
    """Status of question resolution in conversation."""

    PENDING = "pending"
    ANSWERED = "answered"
    SKIPPED = "skipped"
    INFERRED = "inferred"
