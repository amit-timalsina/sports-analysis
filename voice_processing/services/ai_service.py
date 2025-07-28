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
        "exercise_type",
        "exercise_name",
        "duration_minutes",
        "intensity",
        "calories_burned",
        "mental_state",
    ],
    ActivityType.CRICKET_COACHING: [
        "session_type",
        "coach_name",
        "duration_minutes",
        "primary_focus",
        "skills_practiced",
        "discipline_focus",
        "mental_state",
    ],
    ActivityType.CRICKET_MATCH: [
        "match_format",
        "opposition_team",
        "venue",
        "home_away",
        "result",
        "team_name",
        "mental_state",
    ],
    ActivityType.REST_DAY: [
        "rest_type",
        "mental_state",
        "sleep_hours",
        "sleep_quality",
    ],
}


class AIService:
    """Service for ai related operations."""

    def __init__(self, oai_client: AsyncClient) -> None:
        """Initialize the AIService."""
        self.oai_client = oai_client

    def _calculate_completeness_score(
        self, collected_data: dict[str, Any], activity_type: ActivityType
    ) -> float:
        """Calculate data completeness score (0.0 to 1.0)."""
        required_fields = required_fields_by_activity_type.get(activity_type, [])
        if not required_fields:
            return 1.0

        collected_count = sum(
            1 for field in required_fields if collected_data.get(field) is not None
        )
        return collected_count / len(required_fields)

    def _get_rule_based_question(
        self, missing_fields: list[str], activity_type: ActivityType
    ) -> str:
        """Generate rule-based questions for missing fields."""
        if not missing_fields:
            return "Is there anything else you'd like to tell me about your activity?"

        # Take up to 3 fields
        target_fields = missing_fields[:3]

        # Rule-based question templates
        question_templates = {
            "duration_minutes": "How long did your activity last?",
            "intensity": "How intense was it - low, medium, or high?",
            "mental_state": "How did you feel mentally during this?",
            "calories_burned": "How many calories do you think you burned?",
            "exercise_type": "What type of exercise was this?",
            "exercise_name": "What specific exercise did you do?",
            "session_type": "What type of cricket session was this?",
            "coach_name": "Who was your coach?",
            "primary_focus": "What was the main focus of your session?",
            "skills_practiced": "What skills did you practice?",
            "discipline_focus": "Which cricket discipline did you focus on?",
            "match_format": "What format was the match?",
            "opposition_team": "Who did you play against?",
            "venue": "Where was the match played?",
            "home_away": "Was this a home or away match?",
            "result": "What was the result of the match?",
            "team_name": "What's your team name?",
            "rest_type": "What type of rest day was this?",
            "sleep_hours": "How many hours did you sleep?",
            "sleep_quality": "How was your sleep quality?",
        }

        if len(target_fields) == 1:
            field = target_fields[0]
            return question_templates.get(
                field, f"Can you tell me about {field.replace('_', ' ')}?"
            )
        # Combine multiple fields into one question
        field_names = [field.replace("_", " ") for field in target_fields]
        if len(field_names) == 2:
            return f"Can you tell me about {field_names[0]} and {field_names[1]}?"
        return f"Can you tell me about {', '.join(field_names[:-1])}, and {field_names[-1]}?"

    @observe(capture_input=True, capture_output=True)
    async def generate_follow_up_question(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        user_message: str,
        model_name: str,
        turn_number: int = 1,
        use_rule_based: bool = True,
    ) -> FollowUpQuestion | None:
        """Generate a contextual follow-up question using OpenAI or rule-based approach."""
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

        # Take up to 3 fields for the question
        target_fields = missing_fields[:3]
        completeness_score = self._calculate_completeness_score(collected_data, activity_type)

        # Use rule-based questions by default
        if use_rule_based:
            question_text = self._get_rule_based_question(target_fields, activity_type)

            return FollowUpQuestion(
                question=question_text,
                field_targets=target_fields,
                turn_number=turn_number,
                completeness_score=completeness_score,
                collected_data=collected_data,
                is_rule_based=True,
            )

        # AI-generated questions (fallback)
        try:
            activity_value = (
                activity_type.value if hasattr(activity_type, "value") else str(activity_type)
            )

            system_prompt = f"""You are a friendly AI coach talking to a 15-year-old
cricket player in Nepal.

Generate a natural, conversational follow-up question to collect information about: {target_fields}
for {activity_value}.

Context - Already collected: {collected_data}
User message: {user_message}
Missing fields: {target_fields}

Rules:
1. Keep it simple and age-appropriate
2. Sound encouraging and supportive
3. Be specific about what you need
4. Use cricket/fitness terminology they understand
5. Ask about all {len(target_fields)} fields in one natural question

Return ONLY the question text, nothing else."""

            completion = await self.oai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Generate follow-up question for fields: {target_fields}",
                    },
                ],
                temperature=0.7,  # Bit more creative for natural questions
                max_tokens=150,
            )

            question_text = completion.choices[0].message.content or ""
            question_text = question_text.strip().strip('"')

            return FollowUpQuestion(
                question=question_text,
                field_targets=target_fields,
                turn_number=turn_number,
                completeness_score=completeness_score,
                collected_data=collected_data,
                is_rule_based=False,
            )

        except Exception:
            logger.exception("Failed to generate AI follow-up question, falling back to rule-based")

            # Fallback to rule-based
            question_text = self._get_rule_based_question(target_fields, activity_type)

            return FollowUpQuestion(
                question=question_text,
                field_targets=target_fields,
                turn_number=turn_number,
                completeness_score=completeness_score,
                collected_data=collected_data,
                is_rule_based=True,
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
