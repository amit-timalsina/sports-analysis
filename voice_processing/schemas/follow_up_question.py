from pydantic import Field

from common.schemas.app_base_model import AppBaseModel


class FollowUpQuestion(AppBaseModel):
    """Schema for follow-up questions."""

    question: str = Field(..., description="The question text")
    field_target: str = Field(..., description="Target field this question aims to collect")
    question_type: str = Field(..., description="Type of question (direct, clarification, etc.)")
    priority: int = Field(..., description="Question priority (1=highest)")
