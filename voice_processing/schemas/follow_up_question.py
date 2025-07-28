from typing import Any

from pydantic import Field

from common.schemas.app_base_model import AppBaseModel


class FollowUpQuestion(AppBaseModel):
    """Schema for follow-up questions."""

    question: str = Field(..., description="The question text")
    field_targets: list[str] = Field(
        ..., description="Target fields this question aims to collect (max 3)"
    )
    turn_number: int = Field(..., description="Current turn number in the conversation")
    completeness_score: float = Field(..., description="Data completeness score (0.0 to 1.0)")
    collected_data: dict[str, Any] = Field(
        default_factory=dict, description="Data collected so far"
    )
    is_rule_based: bool = Field(
        default=True, description="Whether this question is rule-based or AI-generated"
    )
