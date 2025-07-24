"""Conversation service for managing multi-turn voice interactions."""

import logging
import re
from typing import Any, TypeVar

from langfuse import observe  # type: ignore[import-untyped]
from langfuse.openai import AsyncOpenAI  # type: ignore[import-untyped]
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion

from common.config.settings import settings
from common.exceptions import AppError
from fitness_tracking.schemas.cricket_coaching import (
    CricketCoachingDataExtraction,
)
from fitness_tracking.schemas.cricket_match_data_extraction import CricketMatchDataExtraction
from fitness_tracking.schemas.fitness_data_extraction import FitnessDataExtraction
from fitness_tracking.schemas.rest_day_data_extraction import RestDayDataExtraction
from voice_processing.schemas.conversation_old import (
    ActivityType,
    ConversationAnalysis,
    ConversationContext,
    ConversationResult,
    ConversationState,
    DataCompleteness,
    FollowUpQuestion,
)

logger = logging.getLogger(__name__)

ExtractionModel = TypeVar(
    "ExtractionModel",
    FitnessDataExtraction,
    CricketMatchDataExtraction,
    CricketCoachingDataExtraction,
    RestDayDataExtraction,
)


class ConversationServiceError(AppError):
    """Conversation service specific error."""

    status_code = 500
    detail = "Conversation service operation failed"


class ConversationService:
    """Service for managing multi-turn voice conversations with OpenAI."""

    def __init__(self) -> None:
        """Initialize conversation service."""
        self._client: AsyncOpenAI | None = None
        self.active_conversations: dict[str, ConversationContext] = {}
        self.max_turns = 8  # Maximum conversation turns before forcing completion
        # Maximum times we will ask about any single field before giving up
        self.max_attempts_per_field = 2

        # Define required and optional fields for each activity type
        self.required_fields = {
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

        self.optional_fields = {
            ActivityType.FITNESS: [
                "details",
                "distance_km",
                "location",
                "notes",
            ],
            ActivityType.CRICKET_COACHING: [
                "coach_feedback",
                "skills_practiced",
                "difficulty_level",
                "notes",
            ],
            ActivityType.CRICKET_MATCH: [
                "runs_scored",
                "balls_faced",
                "boundaries_4s",
                "boundaries_6s",
                "how_out",
                "key_shots_played",
                "catches_taken",
                "catches_dropped",
                "stumpings",
                "notes",
            ],
            ActivityType.REST_DAY: [
                "soreness_level",
                "training_reflections",
                "goals_concerns",
                "recovery_activities",
                "notes",
            ],
        }

    def _get_client(self) -> AsyncOpenAI | None:
        """Get OpenAI client, initializing if needed."""
        if self._client is None:
            if settings.app.is_testing or not settings.openai.api_key:  # type: ignore[truthy-function]
                return None

            try:
                self._client = AsyncOpenAI(
                    api_key=settings.openai.api_key,
                    timeout=settings.openai.timeout,
                )
            except (ValueError, TypeError) as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)
                return None

        return self._client

    def _handle_extraction_response(
        self,
        completion: ParsedChatCompletion[ExtractionModel],
        extraction_type: str,
    ) -> ExtractionModel | None:
        """Handle the response from OpenAI extraction parsing."""
        if not completion.choices or not completion.choices[0].message.parsed:
            if completion.choices and completion.choices[0].message.refusal:
                logger.warning(
                    "OpenAI refused to parse %s data: %s",
                    extraction_type,
                    completion.choices[0].message.refusal,
                )
            else:
                logger.warning(
                    "No valid response received from OpenAI for %s extraction",
                    extraction_type,
                )
            return None

        return completion.choices[0].message.parsed

    def start_conversation(
        self,
        session_id: str,
        user_id: str,
        activity_type: ActivityType,
    ) -> ConversationContext:
        """Start a new conversation session."""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            state=ConversationState.STARTED,
        )

        self.active_conversations[session_id] = context
        logger.info("Started conversation for session %s, activity: %s", session_id, activity_type)

        return context

    def get_conversation(self, session_id: str) -> ConversationContext | None:
        """Get existing conversation context."""
        return self.active_conversations.get(session_id)

    async def process_user_input(
        self,
        session_id: str,
        user_input: str,
        transcript_confidence: float = 0.9,
    ) -> ConversationAnalysis:
        """
        Process user input and return conversation analysis.

        Args:
            session_id: Unique session identifier
            user_input: User's voice input (transcript)
            transcript_confidence: Confidence score from speech-to-text

        Returns:
            ConversationAnalysis with next steps for the conversation

        """
        context = self.get_conversation(session_id)
        if not context:
            msg = f"No active conversation for session {session_id}"
            raise ConversationServiceError(msg)

        logger.info(
            "Processing input for session %s (turn %d): %s",
            session_id,
            context.turn_count + 1,
            user_input[:100],
        )

        # Increment turn count and add transcript to history
        context.turn_count += 1

        # Ensure attempt tracking dictionaries exist on the context
        if not hasattr(context, "question_attempts"):
            context.question_attempts = {}

        # **NEW**: Track all transcripts with turn information
        if not hasattr(context, "transcript_history"):
            context.transcript_history = []

        context.transcript_history.append(
            {
                "turn": context.turn_count,
                "transcript": user_input,
                "confidence": transcript_confidence,
            },
        )

        # Extract new data from user input
        extracted_data = await self._extract_data_from_input(
            user_input=user_input,
            activity_type=context.activity_type,
        )

        # Update collected data with new extractions
        context.collected_data.update(extracted_data)

        # Analyze data completeness
        data_completeness = self._analyze_data_completeness(
            context.collected_data,
            context.activity_type,
            transcript_confidence,
        )

        # Filter missing fields based on per-field attempt cap
        remaining_missing = [
            f
            for f in data_completeness.missing_fields
            if context.question_attempts.get(f, 0) < self.max_attempts_per_field
        ]

        # Determine if we should ask follow-up questions (stop if no remaining missing fields)
        should_continue = (
            (not data_completeness.is_complete)
            and context.turn_count < self.max_turns
            and bool(remaining_missing)
        )

        # Generate follow-up question if needed
        next_question = None
        if should_continue and remaining_missing:
            # Pick the highest-priority field (first in remaining list)
            target_field = remaining_missing[0]

            # Increment attempt counter for this field
            context.question_attempts[target_field] = (
                context.question_attempts.get(target_field, 0) + 1
            )

            next_question = await self._generate_follow_up_question(
                context.collected_data,
                context.activity_type,
                [target_field],
            )

        # Create analysis result
        missing_count = len(data_completeness.missing_fields)
        complete_status = (
            "Complete" if data_completeness.is_complete else f"Missing {missing_count} fields"
        )
        analysis = ConversationAnalysis(
            data_completeness=data_completeness,
            next_question=next_question,
            should_continue=should_continue,
            can_generate_final_output=(
                data_completeness.is_complete
                or context.turn_count >= self.max_turns
                or not remaining_missing  # No more fields we can ask about
            ),
            analysis_confidence=data_completeness.confidence_score,
            reasoning=f"Turn {context.turn_count}: {complete_status}",
        )

        logger.info(
            "Analysis for session %s: continue=%s, complete=%s, missing_fields=%s",
            session_id,
            analysis.should_continue,
            analysis.can_generate_final_output,
            data_completeness.missing_fields,
        )

        return analysis

    @observe(capture_input=True, capture_output=True)
    async def _extract_data_from_input(
        self,
        user_input: str,
        activity_type: ActivityType,
    ) -> dict[str, Any]:
        """Extract structured data from user input using OpenAI."""
        client = self._get_client()
        result: dict[str, Any] = {}

        if client is None:
            # Mock response for testing
            result = {
                "mock_field": "mock_value",
                "extracted_from": user_input[:50],
            }
        else:
            try:
                # Route to appropriate extraction method based on activity type
                # Use a dictionary to map activity types to their respective extraction methods
                extraction_methods = {
                    ActivityType.FITNESS: self._extract_fitness_data,
                    ActivityType.CRICKET_MATCH: self._extract_cricket_match_data,
                    ActivityType.CRICKET_COACHING: self._extract_cricket_coaching_data,
                    ActivityType.REST_DAY: self._extract_rest_day_data,
                }
                extraction_method = extraction_methods.get(activity_type)
                if extraction_method:
                    result = await extraction_method(client, user_input)
                else:
                    result = self._fallback_extraction(user_input, activity_type)
            except Exception:
                logger.exception("Failed to extract data from input")
                result = self._fallback_extraction(user_input, activity_type)

        return result

    def _extract_fitness_type(self, user_lower: str) -> str:
        """Extract fitness type from user input."""
        if any(word in user_lower for word in ["run", "running", "jog", "jogging", "sprint"]):
            return "running"
        if any(
            word in user_lower
            for word in ["gym", "weight", "weights", "lift", "lifting", "strength"]
        ):
            return "strength_training"
        if any(word in user_lower for word in ["cricket", "bat", "batting", "wicket", "bowl"]):
            return "cricket_specific"
        if any(
            word in user_lower for word in ["cardio", "cardiovascular", "cycle", "cycling", "swim"]
        ):
            return "cardio"
        if any(
            word in user_lower
            for word in ["stretch", "stretching", "yoga", "flexibility", "pilates"]
        ):
            return "flexibility"
        return "general_fitness"

    def _extract_intensity(self, user_lower: str) -> str:
        """Extract intensity level from user input."""
        if any(word in user_lower for word in ["intense", "hard", "tough", "high", "difficult"]):
            return "high"
        if any(word in user_lower for word in ["easy", "light", "gentle", "low"]):
            return "low"
        return "medium"

    def _fallback_extraction(
        self,
        user_input: str,
        activity_type: ActivityType,
    ) -> dict[str, Any]:
        """Keyword-based extraction as fallback with guaranteed valid values."""
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

        extracted: dict[str, Any] = {}  # Use Any type to support mixed value types
        user_lower = user_input.lower()

        # Simple pattern matching based on activity type
        if activity_type == ActivityType.FITNESS:
            # Ensure we return only valid FitnessType enum values
            fitness_type = self._extract_fitness_type(user_lower)
            extracted["fitness_type"] = fitness_type

            # Extract duration with validation
            duration_match = re.search(r"(\d+)\s*(?:minutes?|mins?)", user_lower)
            if duration_match:
                duration = int(duration_match.group(1))
                extracted["duration_minutes"] = max(1, min(300, duration))  # Ensure valid range

            # Extract intensity with validation - ensure only valid values
            intensity = self._extract_intensity(user_lower)
            extracted["intensity"] = intensity

            # Extract energy level if mentioned
            energy_match = re.search(r"(?:energy|level)\s*(?:was|is|felt)?\s*(\d+)", user_lower)
            if energy_match:
                energy = int(energy_match.group(1))
                extracted["energy_level"] = max(1, min(5, energy))  # Ensure 1-5 range

        extracted["details"] = user_input  # Always capture the full input
        return extracted

    def _analyze_data_completeness(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        transcript_confidence: float,
    ) -> DataCompleteness:
        """Analyze how complete the collected data is."""
        # Defensive programming: handle both enum and string values
        if isinstance(activity_type, str):
            logger.warning(
                "activity_type received as string '%s', converting to enum",
                activity_type,
            )
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                logger.exception("Invalid activity_type string")
                # Fallback to a default
                activity_type = ActivityType.FITNESS

        required = self.required_fields.get(activity_type, [])
        optional = self.optional_fields.get(activity_type, [])

        # Check required fields
        missing_required = [field for field in required if field not in collected_data]
        missing_optional = [field for field in optional if field not in collected_data]

        # Calculate completeness score
        required_score = (
            (len(required) - len(missing_required)) / len(required) if required else 1.0
        )
        optional_score = (
            (len(optional) - len(missing_optional)) / len(optional) if optional else 1.0
        )

        # Weighted score (required fields are more important)
        completeness_score = (required_score * 0.8) + (optional_score * 0.2)

        # Confidence based on transcript quality and data completeness
        confidence = min(transcript_confidence, completeness_score * 1.2)

        # Determine if complete (all required fields present)
        is_complete = len(missing_required) == 0

        return DataCompleteness(
            is_complete=is_complete,
            confidence_score=confidence,
            missing_fields=missing_required + missing_optional[:2],  # Top 2 optional
            collected_fields=list(collected_data.keys()),
            total_required_fields=len(required),
            completeness_percentage=completeness_score * 100.0,
        )

    @observe(capture_input=True, capture_output=True)
    async def _generate_follow_up_question(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        missing_fields: list[str],
    ) -> FollowUpQuestion | None:
        """Generate a contextual follow-up question using OpenAI."""
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

        client = self._get_client()

        # Priority field to ask about
        next_field = missing_fields[0]

        if client is None:
            # Mock question for testing
            return FollowUpQuestion(
                question=f"Can you tell me more about {next_field}?",
                field_target=next_field,
                question_type="required",
                priority=1,
            )

        try:
            system_prompt = f"""You are a friendly AI coach talking to a 15-year-old
cricket player in Nepal.

Generate a natural, conversational follow-up question to collect the "{next_field}"
field for {activity_value}.

Context - Already collected: {collected_data}
Missing field: {next_field}

Rules:
1. Keep it simple and age-appropriate
2. Sound encouraging and supportive
3. Be specific about what you need
4. Use cricket/fitness terminology they understand

Return ONLY the question text, nothing else."""

            completion = await client.chat.completions.create(
                model=settings.openai.gpt_model,
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
                if next_field in self.required_fields.get(activity_type, [])
                else "optional",
                priority=1 if next_field in self.required_fields.get(activity_type, []) else 2,
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

    def complete_conversation(self, session_id: str) -> ConversationResult:
        """Complete the conversation and return final result."""
        context = self.get_conversation(session_id)
        if not context:
            msg = f"No active conversation for session {session_id}"
            raise ConversationServiceError(msg)

        context.state = ConversationState.COMPLETED

        # Calculate quality metrics
        required_fields = self.required_fields.get(context.activity_type, [])
        collected_required = [f for f in required_fields if f in context.collected_data]
        data_quality = len(collected_required) / len(required_fields) if required_fields else 1.0

        # Efficiency: fewer turns is better, but cap at 1.0
        efficiency = min(1.0, max(0.1, 1.0 - (context.turn_count - 2) * 0.1))

        # Ensure final_data includes metadata needed for persistence
        final_data = {
            **context.collected_data,
            "user_id": context.user_id,
            "activity_type": context.activity_type,
            "original_transcript": context.transcript_history[-1]["transcript"]
            if context.transcript_history
            else "",
        }

        result = ConversationResult(
            session_id=session_id,
            final_data=final_data,
            total_turns=context.turn_count,
            completion_status="completed",
            data_quality_score=data_quality,
            conversation_efficiency=efficiency,
        )

        # Clean up
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]

        logger.info(
            "Completed conversation %s: %d turns, %.2f quality, %.2f efficiency",
            session_id,
            result.total_turns,
            result.data_quality_score,
            result.conversation_efficiency,
        )

        return result

    def cleanup_session(self, session_id: str) -> None:
        """Clean up conversation session."""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            logger.info("Cleaned up conversation session: %s", session_id)

    async def _extract_fitness_data(
        self,
        client: AsyncOpenAI,
        user_input: str,
    ) -> dict[str, Any]:
        """Extract fitness data from user input."""
        system_prompt = """You are an expert fitness tracker analyzer for young
cricket players.

CRITICAL:
- You MUST extract fitness data and return it in the EXACT format specified by the schema.
- Don't make up information. Only extract what is present in the transcript.
"""

        completion = await client.beta.chat.completions.parse(
            model=settings.openai.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract fitness data from: {user_input}"},
            ],
            response_format=FitnessDataExtraction,
            temperature=0.1,
            max_tokens=500,
        )

        fitness_data = self._handle_extraction_response(
            completion,
            "fitness",
        )
        if not fitness_data or not isinstance(fitness_data, FitnessDataExtraction):
            return {}

        # Convert to dictionary and filter for only fields mentioned in input
        extracted_data = {}
        if fitness_data.fitness_type:
            extracted_data["fitness_type"] = fitness_data.fitness_type
        if fitness_data.duration_minutes:
            extracted_data["duration_minutes"] = fitness_data.duration_minutes
        if fitness_data.intensity:
            extracted_data["intensity"] = fitness_data.intensity
        if fitness_data.details:
            extracted_data["details"] = fitness_data.details
        if fitness_data.mental_state:
            extracted_data["mental_state"] = fitness_data.mental_state
        if fitness_data.energy_level:
            extracted_data["energy_level"] = fitness_data.energy_level
        if fitness_data.distance_km:
            extracted_data["distance_km"] = fitness_data.distance_km
        if fitness_data.location:
            extracted_data["location"] = fitness_data.location

        logger.info("Extracted structured fitness data: %s", list(extracted_data.keys()))
        return extracted_data

    async def _extract_cricket_match_data(
        self,
        client: AsyncOpenAI,
        user_input: str,
    ) -> dict[str, Any]:
        """Extract cricket match data from user input."""
        system_prompt = """You are an expert cricket match analyzer for young cricket players.

CRITICAL: You MUST extract cricket match data and return it in the EXACT format \
specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For opposition_strength: Use terms like "very weak", "weak", "easy", "average", "strong",
  "tough", "very strong"
- For pre_match_nerves: Use terms like "very nervous", "nervous", "confident",
  "very confident", "excited"
- For post_match_satisfaction: Use terms like "disappointed", "not satisfied",
  "satisfied", "very satisfied"
- For match_type: Use "tournament" for ODI/T20/competitive matches,
  "practice" for friendly matches

Extract only information explicitly mentioned. Use null for missing data."""

        logger.info("🏏 Extracting cricket match data from: '%s'", user_input)
        logger.info("🏏 Using system prompt: %s...", system_prompt[:200])

        completion = await client.beta.chat.completions.parse(
            model=settings.openai.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract cricket match data from: {user_input}"},
            ],
            response_format=CricketMatchDataExtraction,
            temperature=0.1,
            max_tokens=500,
        )

        logger.info(
            "🏏 OpenAI completion response received, choices: %d",
            len(completion.choices),
        )

        cricket_data = self._handle_extraction_response(
            completion,
            "cricket match",
        )
        if not cricket_data or not isinstance(cricket_data, CricketMatchDataExtraction):
            return {}

        logger.info("🏏 Choice message parsed: %s", cricket_data is not None)
        logger.info("🏏 Raw cricket_data object: %s", cricket_data)
        logger.info(
            "🏏 cricket_data.match_type: %s",
            getattr(cricket_data, "match_type", "NOT_SET"),
        )
        logger.info(
            "🏏 cricket_data.runs_scored: %s",
            getattr(cricket_data, "runs_scored", "NOT_SET"),
        )
        logger.info(
            "🏏 cricket_data.balls_faced: %s",
            getattr(cricket_data, "balls_faced", "NOT_SET"),
        )

        extracted_data = {}
        # Add all non-null fields
        field_mappings = [
            ("match_type", "match_type", True),
            ("opposition_strength", "opposition_strength", True),
            ("runs_scored", "runs_scored", False),
            ("balls_faced", "balls_faced", False),
            ("boundaries_4s", "boundaries_4s", False),
            ("boundaries_6s", "boundaries_6s", False),
            ("how_out", "how_out", True),
            ("key_shots_played", "key_shots_played", True),
            ("catches_taken", "catches_taken", False),
            ("catches_dropped", "catches_dropped", False),
            ("stumpings", "stumpings", False),
            ("pre_match_nerves", "pre_match_nerves", True),
            ("post_match_satisfaction", "post_match_satisfaction", True),
            ("mental_state", "mental_state", True),
            ("notes", "notes", True),
        ]

        for attr, key, is_string in field_mappings:
            value = getattr(cricket_data, attr, None)
            if value is not None if not is_string else value:
                extracted_data[key] = value
                if attr in [
                    "match_type",
                    "opposition_strength",
                    "runs_scored",
                    "balls_faced",
                    "boundaries_4s",
                    "boundaries_6s",
                ]:
                    logger.info("🏏 Added %s: %s", key, value)

        logger.info("🏏 Final extracted_data: %s", extracted_data)
        logger.info(
            "Extracted structured cricket match data: %s",
            list(extracted_data.keys()),
        )

        # Filter out 'null' string values
        filtered_data = {k: v for k, v in extracted_data.items() if v != "null" and v is not None}
        logger.info("🏏 Filtered data (removing 'null' values): %s", filtered_data)
        return filtered_data

    async def _extract_cricket_coaching_data(
        self,
        client: AsyncOpenAI,
        user_input: str,
    ) -> dict[str, Any]:
        """Extract cricket coaching data from user input."""
        system_prompt = """You are an expert cricket coaching session analyzer
for young cricket players.

CRITICAL: You MUST extract cricket coaching data and return it in the EXACT format
specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For confidence_level: Use terms like "very low", "low", "confident",
  "very confident"
- For focus_level: Use terms like "distracted", "okay", "focused",
  "very focused"
- For self_rating: Use terms like "poor", "below average", "good",
  "excellent"

Extract only information explicitly mentioned. Use null for missing data."""

        completion = await client.beta.chat.completions.parse(
            model=settings.openai.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Extract cricket coaching data from: {user_input}",
                },
            ],
            response_format=CricketCoachingDataExtraction,
            temperature=0.1,
            max_tokens=500,
        )

        coaching_data = self._handle_extraction_response(
            completion,
            "cricket coaching",
        )
        if not coaching_data or not isinstance(coaching_data, CricketCoachingDataExtraction):
            return {}

        extracted_data = {}
        field_list = [
            "session_type",
            "duration_minutes",
            "what_went_well",
            "areas_for_improvement",
            "skills_practiced",
            "self_assessment_score",
            "confidence_level",
            "focus_level",
            "mental_state",
            "coach_feedback",
            "difficulty_level",
            "learning_satisfaction",
            "notes",
        ]

        for field in field_list:
            value = getattr(coaching_data, field, None)
            if value is not None:
                extracted_data[field] = value

        logger.info(
            "Extracted structured cricket coaching data: %s",
            list(extracted_data.keys()),
        )

        # Filter out 'null' string values
        filtered_data = {k: v for k, v in extracted_data.items() if v != "null" and v is not None}
        logger.info("🏏 Filtered coaching data (removing 'null' values): %s", filtered_data)
        return filtered_data

    async def _extract_rest_day_data(
        self,
        client: AsyncOpenAI,
        user_input: str,
    ) -> dict[str, Any]:
        """Extract rest day data from user input."""
        system_prompt = """\
You are an expert rest day analyzer for young cricket players.

CRITICAL: You MUST extract rest day data and return it in the EXACT format \
specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For fatigue_level: Use terms like "exhausted", "tired", "okay", "fresh", \
"energetic"
- For energy_level: Use terms like "very low", "low", "average", "high", \
"very high"
- For motivation_level: Use terms like "unmotivated", "low", "motivated", \
"very motivated"
- For soreness_level: Use terms like "very sore", "sore", "a bit sore", \
"fine"

Extract only information explicitly mentioned. Use null for missing data."""

        completion = await client.beta.chat.completions.parse(
            model=settings.openai.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract rest day data from: {user_input}"},
            ],
            response_format=RestDayDataExtraction,
            temperature=0.1,
            max_tokens=500,
        )

        rest_data = self._handle_extraction_response(
            completion,
            "rest day",
        )
        if not rest_data or not isinstance(rest_data, RestDayDataExtraction):
            return {}

        extracted_data = {}
        field_list = [
            "rest_type",
            "physical_state",
            "fatigue_level",
            "energy_level",
            "motivation_level",
            "mood_description",
            "mental_state",
            "soreness_level",
            "training_reflections",
            "goals_concerns",
            "recovery_activities",
            "notes",
        ]

        for field in field_list:
            value = getattr(rest_data, field, None)
            if value is not None:
                extracted_data[field] = value

        logger.info("Extracted structured rest day data: %s", list(extracted_data.keys()))

        # Filter out 'null' string values
        filtered_data = {k: v for k, v in extracted_data.items() if v != "null" and v is not None}
        logger.info("😴 Filtered rest day data (removing 'null' values): %s", filtered_data)
        return filtered_data


# Global conversation service instance
conversation_service = ConversationService()
