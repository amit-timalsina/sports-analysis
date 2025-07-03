"""Additional conversation related enums."""

from enum import Enum


class ConversationStage(str, Enum):
    """Stages within data collection process."""

    INITIAL_INPUT = "initial_input"
    BASIC_DATA_COLLECTION = "basic_data_collection"
    DETAILED_DATA_COLLECTION = "detailed_data_collection"
    CLARIFICATION = "clarification"
    VALIDATION = "validation"
    FINALIZATION = "finalization"


class ActivityType(str, Enum):
    """Types of activities the user can log."""

    FITNESS = "fitness"
    CRICKET_COACHING = "cricket_coaching"
    CRICKET_MATCH = "cricket_match"
    REST_DAY = "rest_day"


class MessageType(str, Enum):
    """Types of messages in a conversation."""

    USER_INPUT = "user_input"
    AI_RESPONSE = "ai_response"
    FOLLOW_UP_QUESTION = "follow_up_question"
    CLARIFICATION_REQUEST = "clarification_request"
    VALIDATION_CHECK = "validation_check"
    SYSTEM_MESSAGE = "system_message"


class QuestionType(str, Enum):
    """Types of questions in conversations."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    CLARIFICATION = "clarification"
    VALIDATION = "validation"
    FOLLOW_UP = "follow_up"
