from collections.abc import AsyncGenerator
from typing import Any

import svcs
from langfuse import observe  # type: ignore[import-untyped]
from openai import AsyncClient

from fitness_tracking.schemas.enums.activity_type import ActivityType
from logger import get_logger
from voice_processing.schemas.follow_up_question import FollowUpQuestion
from voice_processing.services.openai_service import OpenAIService

logger = get_logger(__name__)


required_fields_by_activity_type: dict[ActivityType, list[str]] = {
    ActivityType.FITNESS: [
        "fitness_type",
        "duration_minutes",
        "intensity",
        "mental_state",
        "energy_level",
    ],
    ActivityType.CRICKET_COACHING: [
        "session_type",
        "duration_minutes",
        "what_went_well",
        "areas_for_improvement",
        "self_assessment_score",
        "confidence_level",
        "focus_level",
        "learning_satisfaction",
        "mental_state",
    ],
    ActivityType.CRICKET_MATCH: [
        "match_type",
        "opposition_strength",
        "pre_match_nerves",
        "post_match_satisfaction",
        "mental_state",
    ],
    ActivityType.REST_DAY: [
        "rest_type",
        "physical_state",
        "fatigue_level",
        "energy_level",
        "motivation_level",
        "mood_description",
        "mental_state",
    ],
}


class AIService:
    """Service for ai related operations."""

    def __init__(self, oai_client: AsyncClient) -> None:
        """Initialize the AIService."""
        self.oai_client = oai_client

    @observe(capture_input=True, capture_output=True)
    async def generate_follow_up_question(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        user_message: str,
        model_name: str,
    ) -> FollowUpQuestion | None:
        """Generate a contextual follow-up question using OpenAI."""
        required_fields = required_fields_by_activity_type.get(activity_type, [])
        missing_fields = [field for field in required_fields if collected_data.get(field) is None]

        if not missing_fields:
            return None

        # Defensive programming: handle both enum and string values
        if isinstance(activity_type, str):
            logger.warning(
                "activity_type received as string '%s', converting to enum",
                activity_type,
            )
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                logger.exception("Invalid activity_type string: %s", activity_type)
                # Fallback to a default
                activity_type = ActivityType.FITNESS

        activity_value = (
            activity_type.value if hasattr(activity_type, "value") else str(activity_type)
        )

        # Priority field to ask about
        next_field = missing_fields[0]

        try:
            system_prompt = f"""You are a friendly AI coach talking to a 15-year-old
    cricket player in Nepal.

    Generate a natural, conversational follow-up question to collect the "{next_field}"
    field for {activity_value}.

    Context - Already collected: {collected_data}
    User message: {user_message}
    Missing field: {next_field}

    Rules:
    1. Keep it simple and age-appropriate
    2. Sound encouraging and supportive
    3. Be specific about what you need
    4. Use cricket/fitness terminology they understand

    Return ONLY the question text, nothing else."""

            completion = await self.oai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Generate follow-up question for field: {next_field}",
                    },
                ],
                temperature=0.7,  # Bit more creative for natural questions
                max_tokens=100,
            )

            question_text = completion.choices[0].message.content or ""
            question_text = question_text.strip().strip('"')

            return FollowUpQuestion(
                question=question_text,
                field_target=next_field,
                question_type="required"
                if next_field in required_fields_by_activity_type.get(activity_type, [])
                else "optional",
                priority=1
                if next_field in required_fields_by_activity_type.get(activity_type, [])
                else 2,
            )

        except Exception:
            logger.exception("Failed to generate follow-up question")

            # Fallback questions
            fallback_questions = {
                "duration_minutes": "How long did your activity last?",
                "intensity": "How intense was it - low, medium, or high?",
                "mental_state": "How did you feel mentally during this?",
                "energy_level": "What was your energy level from 1 to 5?",
                "fitness_type": "What type of fitness activity was this?",
                "details": "Can you tell me more details about what you did?",
                "what_went_well": "What went well in your practice session?",
                "areas_for_improvement": "What areas do you think you need to improve?",
            }

            fallback_question = fallback_questions.get(
                next_field,
                f"Can you tell me about {next_field.replace('_', ' ')}?",
            )

            return FollowUpQuestion(
                question=fallback_question,
                field_target=next_field,
                question_type="required",
                priority=2,
            )

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["AIService", None]:
        """Get the AIService as a dependency."""
        openai_service = await services.aget(OpenAIService)
        oai_client = openai_service.get_client()
        if oai_client is None:
            msg = "OpenAI client not found"
            raise RuntimeError(msg)
        yield cls(oai_client)
